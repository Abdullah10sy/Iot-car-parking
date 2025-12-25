"""
IoT Smart Parking System - Backend API Server

This Flask application provides REST APIs for the smart parking system,
handles real-time data processing, and manages reservations and payments.
"""

from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import redis
import json
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv
import stripe
import logging

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://user:password@localhost/parking_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Initialize extensions
db = SQLAlchemy(app)
socketio = SocketIO(app, cors_allowed_origins="*")
cors = CORS(app)
jwt = JWTManager(app)

# Initialize Redis
redis_client = redis.Redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379'))

# Initialize Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Models
class ParkingSpot(db.Model):
    __tablename__ = 'parking_spots'
    
    id = db.Column(db.String(50), primary_key=True)  # e.g., PARK_001
    location = db.Column(db.String(100), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    zone = db.Column(db.String(20), nullable=False)
    is_occupied = db.Column(db.Boolean, default=False)
    is_reserved = db.Column(db.Boolean, default=False)
    sensor_type = db.Column(db.String(20), default='ultrasonic')
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    reservations = db.relationship('Reservation', backref='spot', lazy=True)
    sensor_data = db.relationship('SensorData', backref='spot', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'location': self.location,
            'level': self.level,
            'zone': self.zone,
            'is_occupied': self.is_occupied,
            'is_reserved': self.is_reserved,
            'sensor_type': self.sensor_type,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'status': 'occupied' if self.is_occupied else ('reserved' if self.is_reserved else 'available')
        }

class SensorData(db.Model):
    __tablename__ = 'sensor_data'
    
    id = db.Column(db.Integer, primary_key=True)
    sensor_id = db.Column(db.String(50), db.ForeignKey('parking_spots.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    occupied = db.Column(db.Boolean, nullable=False)
    distance_cm = db.Column(db.Float)
    battery_level = db.Column(db.Integer)
    signal_strength = db.Column(db.Integer)
    raw_data = db.Column(db.JSON)
    
    def to_dict(self):
        return {
            'id': self.id,
            'sensor_id': self.sensor_id,
            'timestamp': self.timestamp.isoformat(),
            'occupied': self.occupied,
            'distance_cm': self.distance_cm,
            'battery_level': self.battery_level,
            'signal_strength': self.signal_strength
        }

class Reservation(db.Model):
    __tablename__ = 'reservations'
    
    id = db.Column(db.String(50), primary_key=True)
    spot_id = db.Column(db.String(50), db.ForeignKey('parking_spots.id'), nullable=False)
    user_email = db.Column(db.String(100), nullable=False)
    user_phone = db.Column(db.String(20))
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    duration_hours = db.Column(db.Float, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    payment_status = db.Column(db.String(20), default='pending')  # pending, paid, failed, refunded
    payment_intent_id = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')  # active, completed, cancelled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'spot_id': self.spot_id,
            'user_email': self.user_email,
            'user_phone': self.user_phone,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_hours': self.duration_hours,
            'total_amount': self.total_amount,
            'payment_status': self.payment_status,
            'status': self.status,
            'created_at': self.created_at.isoformat()
        }

# API Routes

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0'
    })

@app.route('/api/spots', methods=['GET'])
def get_parking_spots():
    """Get all parking spots with current status"""
    try:
        spots = ParkingSpot.query.all()
        return jsonify({
            'spots': [spot.to_dict() for spot in spots],
            'total_count': len(spots),
            'available_count': len([s for s in spots if not s.is_occupied and not s.is_reserved]),
            'occupied_count': len([s for s in spots if s.is_occupied]),
            'reserved_count': len([s for s in spots if s.is_reserved])
        })
    except Exception as e:
        logger.error(f"Error fetching parking spots: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/spots/<spot_id>', methods=['GET'])
def get_parking_spot(spot_id):
    """Get specific parking spot details"""
    try:
        spot = ParkingSpot.query.get_or_404(spot_id)
        
        # Get recent sensor data
        recent_data = SensorData.query.filter_by(sensor_id=spot_id)\
                                    .order_by(SensorData.timestamp.desc())\
                                    .limit(10).all()
        
        return jsonify({
            'spot': spot.to_dict(),
            'recent_sensor_data': [data.to_dict() for data in recent_data]
        })
    except Exception as e:
        logger.error(f"Error fetching spot {spot_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/spots/available', methods=['GET'])
def get_available_spots():
    """Get all available parking spots"""
    try:
        level = request.args.get('level')
        zone = request.args.get('zone')
        
        query = ParkingSpot.query.filter_by(is_occupied=False, is_reserved=False)
        
        if level:
            query = query.filter_by(level=level)
        if zone:
            query = query.filter_by(zone=zone)
            
        spots = query.all()
        
        return jsonify({
            'available_spots': [spot.to_dict() for spot in spots],
            'count': len(spots)
        })
    except Exception as e:
        logger.error(f"Error fetching available spots: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/sensor-data', methods=['POST'])
def receive_sensor_data():
    """Receive sensor data from MQTT or direct HTTP"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['sensor_id', 'occupied', 'timestamp']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Process sensor data
        result = process_sensor_data(data)
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"Error processing sensor data: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reservations', methods=['POST'])
def create_reservation():
    """Create a new parking reservation"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['spot_id', 'user_email', 'start_time', 'duration_hours']
        if not all(field in data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Check if spot is available
        spot = ParkingSpot.query.get(data['spot_id'])
        if not spot:
            return jsonify({'error': 'Parking spot not found'}), 404
        
        if spot.is_occupied or spot.is_reserved:
            return jsonify({'error': 'Parking spot not available'}), 400
        
        # Calculate reservation details
        start_time = datetime.fromisoformat(data['start_time'].replace('Z', '+00:00'))
        duration_hours = float(data['duration_hours'])
        end_time = start_time + timedelta(hours=duration_hours)
        
        # Calculate cost (example: $2 per hour)
        hourly_rate = 2.0
        total_amount = duration_hours * hourly_rate
        
        # Create reservation
        reservation_id = f"RES_{int(datetime.utcnow().timestamp())}"
        reservation = Reservation(
            id=reservation_id,
            spot_id=data['spot_id'],
            user_email=data['user_email'],
            user_phone=data.get('user_phone'),
            start_time=start_time,
            end_time=end_time,
            duration_hours=duration_hours,
            total_amount=total_amount
        )
        
        # Create Stripe payment intent
        payment_intent = stripe.PaymentIntent.create(
            amount=int(total_amount * 100),  # Amount in cents
            currency='usd',
            metadata={
                'reservation_id': reservation_id,
                'spot_id': data['spot_id']
            }
        )
        
        reservation.payment_intent_id = payment_intent.id
        
        # Save to database
        db.session.add(reservation)
        spot.is_reserved = True
        db.session.commit()
        
        # Emit real-time update
        socketio.emit('spot_reserved', {
            'spot_id': data['spot_id'],
            'reservation_id': reservation_id
        })
        
        return jsonify({
            'reservation': reservation.to_dict(),
            'client_secret': payment_intent.client_secret
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating reservation: {str(e)}")
        db.session.rollback()
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reservations/<reservation_id>', methods=['GET'])
def get_reservation(reservation_id):
    """Get reservation details"""
    try:
        reservation = Reservation.query.get_or_404(reservation_id)
        return jsonify({'reservation': reservation.to_dict()})
    except Exception as e:
        logger.error(f"Error fetching reservation {reservation_id}: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/analytics/occupancy', methods=['GET'])
def get_occupancy_analytics():
    """Get current occupancy statistics"""
    try:
        total_spots = ParkingSpot.query.count()
        occupied_spots = ParkingSpot.query.filter_by(is_occupied=True).count()
        reserved_spots = ParkingSpot.query.filter_by(is_reserved=True).count()
        available_spots = total_spots - occupied_spots - reserved_spots
        
        occupancy_rate = (occupied_spots / total_spots * 100) if total_spots > 0 else 0
        
        # Get occupancy by level
        levels_data = db.session.query(
            ParkingSpot.level,
            db.func.count(ParkingSpot.id).label('total'),
            db.func.sum(db.case([(ParkingSpot.is_occupied == True, 1)], else_=0)).label('occupied')
        ).group_by(ParkingSpot.level).all()
        
        levels_stats = []
        for level_data in levels_data:
            level, total, occupied = level_data
            levels_stats.append({
                'level': level,
                'total_spots': total,
                'occupied_spots': occupied or 0,
                'available_spots': total - (occupied or 0),
                'occupancy_rate': ((occupied or 0) / total * 100) if total > 0 else 0
            })
        
        return jsonify({
            'overall': {
                'total_spots': total_spots,
                'occupied_spots': occupied_spots,
                'reserved_spots': reserved_spots,
                'available_spots': available_spots,
                'occupancy_rate': round(occupancy_rate, 2)
            },
            'by_level': levels_stats,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error fetching occupancy analytics: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

# Helper Functions

def process_sensor_data(data):
    """Process incoming sensor data and update parking spot status"""
    sensor_id = data['sensor_id']
    occupied = data['occupied']
    timestamp = datetime.fromisoformat(data['timestamp'].replace('Z', '+00:00'))
    
    # Find or create parking spot
    spot = ParkingSpot.query.get(sensor_id)
    if not spot:
        # Create new spot if it doesn't exist
        spot = ParkingSpot(
            id=sensor_id,
            location=data.get('location', f'Unknown_{sensor_id}'),
            level=data.get('level', 'L1'),
            zone=data.get('zone', 'A')
        )
        db.session.add(spot)
    
    # Update spot status
    previous_status = spot.is_occupied
    spot.is_occupied = occupied
    spot.last_updated = timestamp
    
    # Save sensor data
    sensor_data = SensorData(
        sensor_id=sensor_id,
        timestamp=timestamp,
        occupied=occupied,
        distance_cm=data.get('distance_cm'),
        battery_level=data.get('battery_level'),
        signal_strength=data.get('signal_strength'),
        raw_data=data
    )
    
    db.session.add(sensor_data)
    db.session.commit()
    
    # Cache current status in Redis
    redis_client.setex(f"spot:{sensor_id}", 3600, json.dumps({
        'occupied': occupied,
        'last_updated': timestamp.isoformat()
    }))
    
    # Emit real-time update if status changed
    if previous_status != occupied:
        socketio.emit('spot_status_changed', {
            'spot_id': sensor_id,
            'occupied': occupied,
            'timestamp': timestamp.isoformat()
        })
        
        logger.info(f"Spot {sensor_id} status changed: {previous_status} -> {occupied}")
    
    return {
        'status': 'success',
        'spot_id': sensor_id,
        'occupied': occupied,
        'status_changed': previous_status != occupied
    }

# WebSocket Events

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    logger.info('Client connected')
    emit('connected', {'status': 'Connected to parking system'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    logger.info('Client disconnected')

@socketio.on('subscribe_spot')
def handle_subscribe_spot(data):
    """Subscribe to specific spot updates"""
    spot_id = data.get('spot_id')
    if spot_id:
        # Join room for specific spot updates
        from flask_socketio import join_room
        join_room(f"spot_{spot_id}")
        emit('subscribed', {'spot_id': spot_id})

# Initialize database
@app.before_first_request
def create_tables():
    """Create database tables"""
    db.create_all()

if __name__ == '__main__':
    # Run the application
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
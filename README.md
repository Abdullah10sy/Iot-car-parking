# Backend API - IoT Smart Parking System

## Overview

The backend service handles real-time data ingestion from parking sensors, processes the data, stores it in a database, and provides REST APIs for the frontend dashboard and mobile applications.

## Architecture

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   MQTT      │    │   Flask      │    │ PostgreSQL  │
│   Broker    │───▶│   API        │───▶│ Database    │
│             │    │   Server     │    │             │
└─────────────┘    └──────────────┘    └─────────────┘
                           │
                   ┌──────────────┐
                   │   Redis      │
                   │   Cache      │
                   └──────────────┘
```

## Features

- **Real-time Data Ingestion**: MQTT subscriber for sensor data
- **REST API**: RESTful endpoints for parking data and reservations
- **Real-time Updates**: WebSocket support for live dashboard updates
- **Analytics Engine**: Parking trends and occupancy predictions
- **Payment Processing**: Stripe integration for reservations
- **Caching**: Redis for high-performance data access

## Technology Stack

- **Framework**: Flask (Python 3.8+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Message Queue**: MQTT (Mosquitto)
- **Cache**: Redis
- **Payment**: Stripe API
- **Real-time**: Flask-SocketIO
- **Analytics**: Pandas, NumPy, Scikit-learn

## API Endpoints

### Parking Spots
- `GET /api/spots` - List all parking spots
- `GET /api/spots/{spot_id}` - Get specific spot details
- `GET /api/spots/available` - Get available spots
- `POST /api/spots` - Create new parking spot (admin)

### Reservations
- `POST /api/reservations` - Create new reservation
- `GET /api/reservations/{reservation_id}` - Get reservation details
- `PUT /api/reservations/{reservation_id}` - Update reservation
- `DELETE /api/reservations/{reservation_id}` - Cancel reservation

### Analytics
- `GET /api/analytics/occupancy` - Current occupancy statistics
- `GET /api/analytics/trends` - Historical trends
- `GET /api/analytics/predictions` - Occupancy predictions

### Payments
- `POST /api/payments/create-intent` - Create Stripe payment intent
- `POST /api/payments/confirm` - Confirm payment
- `POST /api/webhooks/stripe` - Stripe webhook handler

## Installation

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Setup Database**
   ```bash
   python manage.py init-db
   python manage.py migrate
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start Services**
   ```bash
   # Start MQTT subscriber
   python mqtt_subscriber.py &
   
   # Start Flask API
   python app.py
   ```

## Configuration

Environment variables in `.env`:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `MQTT_BROKER_HOST`: MQTT broker hostname
- `STRIPE_SECRET_KEY`: Stripe API secret key
- `JWT_SECRET_KEY`: JWT token secret

## Testing

```bash
# Run unit tests
python -m pytest tests/

# Run integration tests
python -m pytest tests/integration/

# Test MQTT connectivity
python test_mqtt.py
```
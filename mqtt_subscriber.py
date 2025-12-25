"""
MQTT Subscriber for IoT Smart Parking System

This service subscribes to MQTT topics to receive real-time sensor data
from parking sensors and processes the data through the backend API.
"""

import paho.mqtt.client as mqtt
import json
import requests
import logging
import os
import time
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
MQTT_BROKER_HOST = os.getenv('MQTT_BROKER_HOST', 'localhost')
MQTT_BROKER_PORT = int(os.getenv('MQTT_BROKER_PORT', 1883))
MQTT_USERNAME = os.getenv('MQTT_USERNAME', 'parking_system')
MQTT_PASSWORD = os.getenv('MQTT_PASSWORD', 'mqtt_password')
MQTT_KEEPALIVE = int(os.getenv('MQTT_KEEPALIVE', 60))

# API Configuration
API_BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:5000')
API_SENSOR_ENDPOINT = f"{API_BASE_URL}/api/sensor-data"

# MQTT Topics
TOPIC_SENSOR_STATUS = "parking/sensor/+/status"
TOPIC_SENSOR_HEARTBEAT = "parking/sensor/+/heartbeat"
TOPIC_SENSOR_ERROR = "parking/sensor/+/error"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ParkingMQTTSubscriber:
    """MQTT Subscriber for parking sensor data"""
    
    def __init__(self):
        self.client = mqtt.Client()
        self.client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Set callback functions
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.on_disconnect = self.on_disconnect
        self.client.on_subscribe = self.on_subscribe
        
        # Statistics
        self.messages_received = 0
        self.messages_processed = 0
        self.errors_count = 0
        self.start_time = datetime.utcnow()
        
    def on_connect(self, client, userdata, flags, rc):
        """Callback for when the client receives a CONNACK response from the server"""
        if rc == 0:
            logger.info("Connected to MQTT broker successfully")
            
            # Subscribe to all sensor topics
            topics = [
                (TOPIC_SENSOR_STATUS, 1),      # QoS 1 for sensor status
                (TOPIC_SENSOR_HEARTBEAT, 0),   # QoS 0 for heartbeat
                (TOPIC_SENSOR_ERROR, 1)        # QoS 1 for errors
            ]
            
            for topic, qos in topics:
                client.subscribe(topic, qos)
                logger.info(f"Subscribed to topic: {topic} (QoS {qos})")
                
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
            
    def on_disconnect(self, client, userdata, rc):
        """Callback for when the client disconnects from the server"""
        if rc != 0:
            logger.warning("Unexpected disconnection from MQTT broker")
        else:
            logger.info("Disconnected from MQTT broker")
            
    def on_subscribe(self, client, userdata, mid, granted_qos):
        """Callback for when the client receives a SUBACK response from the server"""
        logger.info(f"Subscription confirmed with QoS: {granted_qos}")
        
    def on_message(self, client, userdata, msg):
        """Callback for when a PUBLISH message is received from the server"""
        try:
            self.messages_received += 1
            
            # Decode message
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.debug(f"Received message on topic {topic}: {payload}")
            
            # Parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in message: {e}")
                self.errors_count += 1
                return
                
            # Process message based on topic type
            if "/status" in topic:
                self.process_sensor_status(data)
            elif "/heartbeat" in topic:
                self.process_sensor_heartbeat(data)
            elif "/error" in topic:
                self.process_sensor_error(data)
            else:
                logger.warning(f"Unknown topic: {topic}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.errors_count += 1
            
    def process_sensor_status(self, data):
        """Process sensor status messages"""
        try:
            # Validate required fields
            required_fields = ['sensor_id', 'occupied', 'timestamp']
            if not all(field in data for field in required_fields):
                logger.error(f"Missing required fields in sensor data: {data}")
                return
                
            # Add processing timestamp
            data['processed_at'] = datetime.utcnow().isoformat()
            
            # Send to API
            response = requests.post(
                API_SENSOR_ENDPOINT,
                json=data,
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                self.messages_processed += 1
                result = response.json()
                
                if result.get('status_changed'):
                    logger.info(f"Spot {data['sensor_id']} status changed to: "
                              f"{'OCCUPIED' if data['occupied'] else 'FREE'}")
                else:
                    logger.debug(f"Spot {data['sensor_id']} status confirmed: "
                               f"{'OCCUPIED' if data['occupied'] else 'FREE'}")
            else:
                logger.error(f"API request failed: {response.status_code} - {response.text}")
                self.errors_count += 1
                
        except requests.RequestException as e:
            logger.error(f"Error sending data to API: {e}")
            self.errors_count += 1
        except Exception as e:
            logger.error(f"Error processing sensor status: {e}")
            self.errors_count += 1
            
    def process_sensor_heartbeat(self, data):
        """Process sensor heartbeat messages"""
        try:
            sensor_id = data.get('sensor_id')
            status = data.get('status')
            
            if sensor_id and status:
                logger.debug(f"Heartbeat from {sensor_id}: {status}")
                
                # Could store heartbeat data or update sensor health status
                # For now, just log it
                
        except Exception as e:
            logger.error(f"Error processing heartbeat: {e}")
            
    def process_sensor_error(self, data):
        """Process sensor error messages"""
        try:
            sensor_id = data.get('sensor_id')
            error_type = data.get('error')
            timestamp = data.get('timestamp')
            
            logger.warning(f"Sensor error from {sensor_id}: {error_type} at {timestamp}")
            
            # Could implement error handling logic here:
            # - Send alerts
            # - Update sensor status
            # - Trigger maintenance notifications
            
        except Exception as e:
            logger.error(f"Error processing sensor error: {e}")
            
    def get_statistics(self):
        """Get subscriber statistics"""
        uptime = datetime.utcnow() - self.start_time
        
        return {
            'uptime_seconds': uptime.total_seconds(),
            'messages_received': self.messages_received,
            'messages_processed': self.messages_processed,
            'errors_count': self.errors_count,
            'success_rate': (self.messages_processed / self.messages_received * 100) 
                          if self.messages_received > 0 else 0
        }
        
    def connect_and_loop(self):
        """Connect to MQTT broker and start the message loop"""
        try:
            logger.info(f"Connecting to MQTT broker at {MQTT_BROKER_HOST}:{MQTT_BROKER_PORT}")
            
            # Connect to broker
            self.client.connect(MQTT_BROKER_HOST, MQTT_BROKER_PORT, MQTT_KEEPALIVE)
            
            # Start the loop
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, shutting down...")
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error in MQTT loop: {e}")
            
    def disconnect(self):
        """Disconnect from MQTT broker"""
        self.client.disconnect()
        logger.info("Disconnected from MQTT broker")

def main():
    """Main function"""
    logger.info("Starting MQTT Subscriber for IoT Smart Parking System")
    
    # Create subscriber instance
    subscriber = ParkingMQTTSubscriber()
    
    try:
        # Start the subscriber
        subscriber.connect_and_loop()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        # Print final statistics
        stats = subscriber.get_statistics()
        logger.info(f"Final statistics: {stats}")

if __name__ == "__main__":
    main()
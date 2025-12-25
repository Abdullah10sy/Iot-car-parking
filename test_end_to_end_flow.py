"""
End-to-End Integration Tests for IoT Smart Parking System

This test suite validates the complete system workflow from sensor data
to user interface, including all major components and integrations.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Test utilities
from tests.utils.mqtt_client import TestMQTTClient
from tests.utils.api_client import TestAPIClient
from tests.utils.sensor_simulator import SensorSimulator
from tests.utils.payment_mock import MockStripeService

# Test fixtures
from tests.fixtures.parking_data import SAMPLE_SPOTS, SAMPLE_SENSOR_DATA


class TestEndToEndFlow:
    """Complete end-to-end system testing"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.mqtt_client = TestMQTTClient()
        self.api_client = TestAPIClient()
        self.sensor_simulator = SensorSimulator()
        self.stripe_mock = MockStripeService()
        
        # Initialize test database
        self.api_client.init_test_db()
        
        # Setup test parking spots
        for spot_data in SAMPLE_SPOTS:
            self.api_client.create_spot(spot_data)
    
    def teardown(self):
        """Cleanup after tests"""
        self.api_client.cleanup_test_db()
        self.mqtt_client.disconnect()
    
    def test_complete_sensor_to_dashboard_flow(self):
        """Test: Sensor data → MQTT → Backend → Database → Frontend"""
        
        # Step 1: Simulate sensor reading
        spot_id = "PARK_001"
        sensor_data = {
            "sensor_id": spot_id,
            "timestamp": datetime.utcnow().isoformat(),
            "occupied": True,
            "distance_cm": 45.2,
            "battery_level": 85,
            "signal_strength": -42
        }
        
        # Step 2: Publish sensor data via MQTT
        topic = f"parking/sensor/{spot_id}/status"
        self.mqtt_client.publish(topic, json.dumps(sensor_data))
        
        # Step 3: Wait for backend processing
        time.sleep(2)
        
        # Step 4: Verify spot status updated in database
        spot = self.api_client.get_spot(spot_id)
        assert spot["spot"]["is_occupied"] == True
        assert spot["spot"]["last_updated"] is not None
        
        # Step 5: Verify sensor data stored
        assert len(spot["recent_sensor_data"]) > 0
        latest_data = spot["recent_sensor_data"][0]
        assert latest_data["occupied"] == True
        assert latest_data["distance_cm"] == 45.2
        
        # Step 6: Verify real-time update sent via WebSocket
        # (This would require WebSocket client testing)
        
        print("✓ Complete sensor data flow test passed")
    
    def test_reservation_and_payment_flow(self):
        """Test: Spot selection → Reservation → Payment → Confirmation"""
        
        # Step 1: Get available spots
        available_spots = self.api_client.get_available_spots()
        assert len(available_spots["available_spots"]) > 0
        
        selected_spot = available_spots["available_spots"][0]
        
        # Step 2: Create reservation
        reservation_data = {
            "spot_id": selected_spot["id"],
            "user_email": "test@example.com",
            "user_name": "Test User",
            "user_phone": "+1234567890",
            "start_time": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
            "duration_hours": 2.0
        }
        
        with patch('stripe.PaymentIntent.create', return_value=self.stripe_mock.create_payment_intent(400, {})):
            reservation = self.api_client.create_reservation(reservation_data)
        
        assert reservation["reservation"]["spot_id"] == selected_spot["id"]
        assert reservation["reservation"]["total_amount"] == 4.0  # 2 hours * $2/hour
        assert "client_secret" in reservation
        
        # Step 3: Verify spot is now reserved
        spot = self.api_client.get_spot(selected_spot["id"])
        assert spot["spot"]["is_reserved"] == True
        
        # Step 4: Simulate payment confirmation
        payment_intent_id = reservation["reservation"]["payment_intent_id"]
        
        with patch('stripe.PaymentIntent.confirm', return_value=self.stripe_mock.confirm_payment(payment_intent_id)):
            payment_result = self.api_client.confirm_payment(payment_intent_id)
        
        # Step 5: Verify reservation status updated
        updated_reservation = self.api_client.get_reservation(reservation["reservation"]["id"])
        assert updated_reservation["reservation"]["payment_status"] == "paid"
        
        print("✓ Complete reservation and payment flow test passed")
    
    def test_multiple_sensor_updates_concurrent(self):
        """Test: Multiple sensors sending data simultaneously"""
        
        import concurrent.futures
        
        def send_sensor_update(spot_id, occupied):
            sensor_data = {
                "sensor_id": spot_id,
                "timestamp": datetime.utcnow().isoformat(),
                "occupied": occupied,
                "distance_cm": 50.0 if occupied else 250.0,
                "battery_level": 80 + (hash(spot_id) % 20),  # Random but deterministic
                "signal_strength": -40 - (hash(spot_id) % 20)
            }
            
            topic = f"parking/sensor/{spot_id}/status"
            self.mqtt_client.publish(topic, json.dumps(sensor_data))
            return spot_id
        
        # Simulate 10 sensors updating simultaneously
        spot_ids = [f"PARK_{i:03d}" for i in range(1, 11)]
        occupancy_states = [i % 2 == 0 for i in range(10)]  # Alternating occupied/free
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(send_sensor_update, spot_id, occupied)
                for spot_id, occupied in zip(spot_ids, occupancy_states)
            ]
            
            results = [future.result() for future in futures]
        
        # Wait for all updates to process
        time.sleep(3)
        
        # Verify all spots updated correctly
        for spot_id, expected_occupied in zip(spot_ids, occupancy_states):
            spot = self.api_client.get_spot(spot_id)
            assert spot["spot"]["is_occupied"] == expected_occupied
        
        print("✓ Concurrent sensor updates test passed")
    
    def test_analytics_data_generation(self):
        """Test: Sensor data → Analytics processing → Dashboard metrics"""
        
        # Step 1: Generate historical sensor data
        for i in range(24):  # 24 hours of data
            timestamp = datetime.utcnow() - timedelta(hours=i)
            
            for spot_id in ["PARK_001", "PARK_002", "PARK_003"]:
                # Simulate varying occupancy throughout the day
                occupied = (i >= 8 and i <= 18) and (hash(f"{spot_id}_{i}") % 3 != 0)
                
                sensor_data = {
                    "sensor_id": spot_id,
                    "timestamp": timestamp.isoformat(),
                    "occupied": occupied,
                    "distance_cm": 50.0 if occupied else 250.0,
                    "battery_level": 85,
                    "signal_strength": -45
                }
                
                # Send directly to API (simulating processed MQTT data)
                self.api_client.send_sensor_data(sensor_data)
        
        # Step 2: Get analytics data
        analytics = self.api_client.get_occupancy_analytics()
        
        # Step 3: Verify analytics calculations
        assert "overall" in analytics
        assert "by_level" in analytics
        assert analytics["overall"]["total_spots"] >= 3
        
        # Step 4: Get occupancy trends
        trends = self.api_client.get_occupancy_trends("24h")
        assert len(trends["hourly_data"]) > 0
        
        print("✓ Analytics data generation test passed")
    
    def test_sensor_error_handling(self):
        """Test: Sensor error → Error logging → Alert generation"""
        
        spot_id = "PARK_001"
        
        # Step 1: Send sensor error message
        error_data = {
            "sensor_id": spot_id,
            "error": "sensor_read_error",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        topic = f"parking/sensor/{spot_id}/error"
        self.mqtt_client.publish(topic, json.dumps(error_data))
        
        # Step 2: Wait for processing
        time.sleep(1)
        
        # Step 3: Verify error logged in system events
        events = self.api_client.get_system_events(limit=10)
        error_events = [e for e in events if e.get("event_type") == "sensor_error"]
        assert len(error_events) > 0
        
        latest_error = error_events[0]
        assert latest_error["entity_id"] == spot_id
        
        print("✓ Sensor error handling test passed")
    
    def test_system_performance_under_load(self):
        """Test: System performance with high sensor data volume"""
        
        import time
        
        start_time = time.time()
        
        # Generate high volume of sensor updates
        for batch in range(10):  # 10 batches
            batch_data = []
            
            for i in range(50):  # 50 sensors per batch
                spot_id = f"PARK_{(batch * 50 + i + 1):03d}"
                sensor_data = {
                    "sensor_id": spot_id,
                    "timestamp": datetime.utcnow().isoformat(),
                    "occupied": (batch + i) % 3 == 0,
                    "distance_cm": 100.0 + (i * 10),
                    "battery_level": 80 + (i % 20),
                    "signal_strength": -40 - (i % 30)
                }
                batch_data.append(sensor_data)
            
            # Send batch via MQTT
            for data in batch_data:
                topic = f"parking/sensor/{data['sensor_id']}/status"
                self.mqtt_client.publish(topic, json.dumps(data))
            
            # Small delay between batches
            time.sleep(0.1)
        
        # Wait for all processing to complete
        time.sleep(5)
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Verify system handled the load
        assert processing_time < 30  # Should complete within 30 seconds
        
        # Verify data integrity
        analytics = self.api_client.get_occupancy_analytics()
        assert analytics["overall"]["total_spots"] >= 500
        
        print(f"✓ Performance test passed - processed 500 updates in {processing_time:.2f}s")
    
    def test_reservation_expiry_handling(self):
        """Test: Reservation expiry → Automatic cleanup → Spot availability"""
        
        # Step 1: Create a reservation that expires soon
        spot_id = "PARK_001"
        reservation_data = {
            "spot_id": spot_id,
            "user_email": "test@example.com",
            "start_time": (datetime.utcnow() - timedelta(hours=2)).isoformat(),
            "duration_hours": 1.0  # Already expired
        }
        
        with patch('stripe.PaymentIntent.create', return_value=self.stripe_mock.create_payment_intent(200, {})):
            reservation = self.api_client.create_reservation(reservation_data)
        
        # Step 2: Trigger expiry cleanup (normally done by scheduled task)
        self.api_client.expire_old_reservations()
        
        # Step 3: Verify reservation marked as expired
        updated_reservation = self.api_client.get_reservation(reservation["reservation"]["id"])
        assert updated_reservation["reservation"]["status"] == "expired"
        
        # Step 4: Verify spot is available again
        spot = self.api_client.get_spot(spot_id)
        assert spot["spot"]["is_reserved"] == False
        
        print("✓ Reservation expiry handling test passed")
    
    def test_websocket_real_time_updates(self):
        """Test: Real-time updates via WebSocket"""
        
        # This test would require WebSocket client implementation
        # For now, we'll test the event emission logic
        
        spot_id = "PARK_001"
        
        # Mock WebSocket emission
        with patch('flask_socketio.emit') as mock_emit:
            # Send sensor update
            sensor_data = {
                "sensor_id": spot_id,
                "timestamp": datetime.utcnow().isoformat(),
                "occupied": True,
                "distance_cm": 45.0,
                "battery_level": 85,
                "signal_strength": -42
            }
            
            self.api_client.send_sensor_data(sensor_data)
            
            # Wait for processing
            time.sleep(1)
            
            # Verify WebSocket event was emitted
            mock_emit.assert_called()
            
            # Check the emitted event
            call_args = mock_emit.call_args_list
            spot_events = [call for call in call_args if 'spot_status_changed' in str(call)]
            assert len(spot_events) > 0
        
        print("✓ WebSocket real-time updates test passed")


if __name__ == "__main__":
    # Run specific test
    test_suite = TestEndToEndFlow()
    test_suite.setup()
    
    try:
        test_suite.test_complete_sensor_to_dashboard_flow()
        test_suite.test_reservation_and_payment_flow()
        test_suite.test_multiple_sensor_updates_concurrent()
        test_suite.test_analytics_data_generation()
        test_suite.test_sensor_error_handling()
        test_suite.test_system_performance_under_load()
        test_suite.test_reservation_expiry_handling()
        test_suite.test_websocket_real_time_updates()
        
        print("\n🎉 All end-to-end tests passed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        raise
    finally:
        test_suite.teardown()
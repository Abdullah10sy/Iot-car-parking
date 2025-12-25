/*
 * Configuration file for ESP32 Ultrasonic Parking Sensor
 * 
 * Copy this file and update with your specific settings
 */

#ifndef CONFIG_H
#define CONFIG_H

// Wi-Fi Configuration
#define WIFI_SSID "YourWiFiNetwork"
#define WIFI_PASSWORD "YourWiFiPassword"
#define WIFI_TIMEOUT_MS 20000

// MQTT Configuration
#define MQTT_SERVER "your-mqtt-broker.com"
#define MQTT_PORT 1883
#define MQTT_USER "parking_sensor"
#define MQTT_PASSWORD "your_mqtt_password"
#define MQTT_CLIENT_ID_PREFIX "ParkingSensor_"

// Sensor Configuration
#define SENSOR_ID "PARK_001"  // Unique identifier for this sensor
#define LOCATION "Level_1_Spot_A1"  // Human-readable location
#define OCCUPIED_THRESHOLD_CM 200   // Distance threshold for occupied detection
#define MEASUREMENT_SAMPLES 5       // Number of samples for averaging
#define MEASUREMENT_INTERVAL_MS 30000  // 30 seconds between measurements
#define DEBOUNCE_COUNT 3           // Consecutive readings required for state change

// Hardware Pin Configuration
#define TRIGGER_PIN 5
#define ECHO_PIN 18
#define LED_PIN 2
#define BATTERY_PIN A0  // Analog pin for battery monitoring

// Power Management
#define DEEP_SLEEP_ENABLED false
#define DEEP_SLEEP_TIME_US 300000000  // 5 minutes in microseconds
#define LOW_BATTERY_THRESHOLD 20      // Percentage

// MQTT Topics
#define TOPIC_STATUS "parking/sensor/%s/status"
#define TOPIC_HEARTBEAT "parking/sensor/%s/heartbeat"
#define TOPIC_ERROR "parking/sensor/%s/error"
#define TOPIC_CONFIG "parking/config/%s"

// Sensor Limits
#define MIN_DISTANCE_CM 2     // Minimum valid distance
#define MAX_DISTANCE_CM 400   // Maximum valid distance
#define SENSOR_TIMEOUT_US 30000  // Ultrasonic sensor timeout

// Firmware Information
#define FIRMWARE_VERSION "1.0.0"
#define HARDWARE_VERSION "ESP32_HC-SR04_v1"

#endif
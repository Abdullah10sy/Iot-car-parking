/*
 * IoT Smart Parking System - ESP32 Ultrasonic Sensor
 * 
 * This code reads ultrasonic sensor data to detect parking space occupancy
 * and transmits the data via MQTT to the cloud processing system.
 * 
 * Hardware: ESP32 + HC-SR04 Ultrasonic Sensor
 * Communication: Wi-Fi + MQTT
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <esp_sleep.h>

// Pin definitions
#define TRIGGER_PIN 5
#define ECHO_PIN 18
#define LED_PIN 2

// Sensor configuration
#define OCCUPIED_THRESHOLD_CM 200  // Distance threshold for occupied detection
#define MEASUREMENT_SAMPLES 5      // Number of samples for averaging
#define MEASUREMENT_INTERVAL 30000 // 30 seconds between measurements
#define DEEP_SLEEP_TIME 300000000  // 5 minutes in microseconds

// Wi-Fi credentials (move to config.h in production)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// MQTT configuration
const char* mqtt_server = "your-mqtt-broker.com";
const int mqtt_port = 1883;
const char* mqtt_user = "parking_sensor";
const char* mqtt_password = "sensor_password";

// Device configuration
const char* sensor_id = "PARK_001";  // Unique sensor identifier
const char* location = "Level_1_Spot_A1";

WiFiClient espClient;
PubSubClient client(espClient);

// Global variables
bool current_occupied = false;
bool previous_occupied = false;
unsigned long last_measurement = 0;
int consecutive_readings = 0;
const int DEBOUNCE_COUNT = 3;  // Require 3 consistent readings

void setup() {
  Serial.begin(115200);
  
  // Initialize pins
  pinMode(TRIGGER_PIN, OUTPUT);
  pinMode(ECHO_PIN, INPUT);
  pinMode(LED_PIN, OUTPUT);
  
  // Initialize sensor
  digitalWrite(TRIGGER_PIN, LOW);
  
  Serial.println("IoT Smart Parking Sensor Starting...");
  Serial.printf("Sensor ID: %s\n", sensor_id);
  Serial.printf("Location: %s\n", location);
  
  // Connect to Wi-Fi
  setupWiFi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  
  // Initial sensor reading
  performSensorReading();
  
  Serial.println("Setup complete. Starting main loop...");
}

void loop() {
  // Maintain MQTT connection
  if (!client.connected()) {
    reconnectMQTT();
  }
  client.loop();
  
  // Check if it's time for a new measurement
  if (millis() - last_measurement >= MEASUREMENT_INTERVAL) {
    performSensorReading();
    last_measurement = millis();
  }
  
  // Optional: Enter deep sleep to save power
  // enterDeepSleep();
  
  delay(1000);  // Small delay for stability
}

void setupWiFi() {
  delay(10);
  Serial.println();
  Serial.print("Connecting to ");
  Serial.println(ssid);
  
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("");
    Serial.println("WiFi connected");
    Serial.println("IP address: ");
    Serial.println(WiFi.localIP());
    Serial.printf("Signal strength: %d dBm\n", WiFi.RSSI());
  } else {
    Serial.println("Failed to connect to WiFi");
    // Could implement fallback or retry logic here
  }
}

void reconnectMQTT() {
  while (!client.connected()) {
    Serial.print("Attempting MQTT connection...");
    
    // Create client ID with sensor ID
    String clientId = "ParkingSensor_";
    clientId += sensor_id;
    
    if (client.connect(clientId.c_str(), mqtt_user, mqtt_password)) {
      Serial.println("connected");
      
      // Subscribe to configuration topic for remote updates
      String config_topic = "parking/config/" + String(sensor_id);
      client.subscribe(config_topic.c_str());
      
      // Send online status
      publishStatus("online");
      
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" try again in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("Message arrived [");
  Serial.print(topic);
  Serial.print("] ");
  
  String message;
  for (int i = 0; i < length; i++) {
    message += (char)payload[i];
  }
  Serial.println(message);
  
  // Handle configuration updates
  if (String(topic).indexOf("config") > 0) {
    handleConfigUpdate(message);
  }
}

float measureDistance() {
  // Clear trigger pin
  digitalWrite(TRIGGER_PIN, LOW);
  delayMicroseconds(2);
  
  // Send 10μs pulse
  digitalWrite(TRIGGER_PIN, HIGH);
  delayMicroseconds(10);
  digitalWrite(TRIGGER_PIN, LOW);
  
  // Read echo pin
  long duration = pulseIn(ECHO_PIN, HIGH, 30000);  // 30ms timeout
  
  if (duration == 0) {
    Serial.println("Sensor timeout - no echo received");
    return -1;  // Error value
  }
  
  // Calculate distance in cm (speed of sound = 343 m/s)
  float distance = (duration * 0.0343) / 2;
  
  return distance;
}

float getAverageDistance() {
  float total = 0;
  int valid_readings = 0;
  
  for (int i = 0; i < MEASUREMENT_SAMPLES; i++) {
    float distance = measureDistance();
    
    if (distance > 0 && distance < 400) {  // Valid range for HC-SR04
      total += distance;
      valid_readings++;
    }
    
    delay(100);  // Small delay between measurements
  }
  
  if (valid_readings == 0) {
    return -1;  // No valid readings
  }
  
  return total / valid_readings;
}

void performSensorReading() {
  Serial.println("\n--- Performing sensor reading ---");
  
  // Get averaged distance measurement
  float distance = getAverageDistance();
  
  if (distance < 0) {
    Serial.println("Error: Could not get valid sensor reading");
    publishError("sensor_read_error");
    return;
  }
  
  Serial.printf("Average distance: %.2f cm\n", distance);
  
  // Determine occupancy status
  bool is_occupied = (distance < OCCUPIED_THRESHOLD_CM);
  
  // Implement debouncing logic
  if (is_occupied == current_occupied) {
    consecutive_readings++;
  } else {
    consecutive_readings = 1;
    current_occupied = is_occupied;
  }
  
  // Only update status if we have enough consecutive readings
  if (consecutive_readings >= DEBOUNCE_COUNT) {
    if (current_occupied != previous_occupied) {
      Serial.printf("Status change detected: %s -> %s\n", 
                   previous_occupied ? "OCCUPIED" : "FREE",
                   current_occupied ? "OCCUPIED" : "FREE");
      
      previous_occupied = current_occupied;
      
      // Update LED indicator
      digitalWrite(LED_PIN, current_occupied ? HIGH : LOW);
    }
    
    // Publish sensor data
    publishSensorData(distance, current_occupied);
  }
  
  Serial.printf("Current status: %s (confidence: %d/%d)\n", 
               current_occupied ? "OCCUPIED" : "FREE", 
               consecutive_readings, DEBOUNCE_COUNT);
}

void publishSensorData(float distance, bool occupied) {
  // Create JSON payload
  StaticJsonDocument<300> doc;
  
  doc["sensor_id"] = sensor_id;
  doc["location"] = location;
  doc["timestamp"] = WiFi.getTime();  // Unix timestamp
  doc["occupied"] = occupied;
  doc["distance_cm"] = round(distance * 100) / 100.0;  // Round to 2 decimal places
  doc["battery_level"] = getBatteryLevel();
  doc["signal_strength"] = WiFi.RSSI();
  doc["firmware_version"] = "1.0.0";
  
  String payload;
  serializeJson(doc, payload);
  
  // Publish to MQTT topic
  String topic = "parking/sensor/" + String(sensor_id) + "/status";
  
  if (client.publish(topic.c_str(), payload.c_str(), true)) {  // Retain message
    Serial.println("Data published successfully:");
    Serial.println(payload);
  } else {
    Serial.println("Failed to publish data");
  }
}

void publishStatus(const char* status) {
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["status"] = status;
  doc["timestamp"] = WiFi.getTime();
  doc["ip_address"] = WiFi.localIP().toString();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "parking/sensor/" + String(sensor_id) + "/heartbeat";
  client.publish(topic.c_str(), payload.c_str());
}

void publishError(const char* error_type) {
  StaticJsonDocument<200> doc;
  doc["sensor_id"] = sensor_id;
  doc["error"] = error_type;
  doc["timestamp"] = WiFi.getTime();
  
  String payload;
  serializeJson(doc, payload);
  
  String topic = "parking/sensor/" + String(sensor_id) + "/error";
  client.publish(topic.c_str(), payload.c_str());
}

void handleConfigUpdate(String config) {
  // Parse configuration JSON and update settings
  StaticJsonDocument<200> doc;
  deserializeJson(doc, config);
  
  if (doc.containsKey("measurement_interval")) {
    // Update measurement interval (implement as needed)
    Serial.println("Configuration updated");
  }
}

int getBatteryLevel() {
  // Placeholder for battery level reading
  // Implement based on your power management setup
  return 85;  // Return percentage
}

void enterDeepSleep() {
  Serial.println("Entering deep sleep mode...");
  
  // Configure wake-up timer
  esp_sleep_enable_timer_wakeup(DEEP_SLEEP_TIME);
  
  // Enter deep sleep
  esp_deep_sleep_start();
}
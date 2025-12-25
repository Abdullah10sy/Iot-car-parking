-- IoT Smart Parking System Database Schema
-- PostgreSQL Database Schema

-- Create database (run as superuser)
-- CREATE DATABASE parking_db;
-- CREATE USER parking_user WITH PASSWORD 'secure_password';
-- GRANT ALL PRIVILEGES ON DATABASE parking_db TO parking_user;

-- Connect to parking_db database before running the rest

-- Enable UUID extension for generating unique IDs
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Parking Spots Table
CREATE TABLE parking_spots (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., PARK_001, PARK_002
    location VARCHAR(100) NOT NULL,  -- Human readable location
    level VARCHAR(20) NOT NULL,  -- Parking level (L1, L2, B1, etc.)
    zone VARCHAR(20) NOT NULL,   -- Zone within level (A, B, C, etc.)
    spot_number INTEGER,         -- Spot number within zone
    is_occupied BOOLEAN DEFAULT FALSE,
    is_reserved BOOLEAN DEFAULT FALSE,
    is_disabled BOOLEAN DEFAULT FALSE,  -- For maintenance
    sensor_type VARCHAR(20) DEFAULT 'ultrasonic',  -- ultrasonic, magnetic, camera, infrared
    coordinates_x DECIMAL(10,6),  -- For mapping (optional)
    coordinates_y DECIMAL(10,6),  -- For mapping (optional)
    hourly_rate DECIMAL(8,2) DEFAULT 2.00,  -- Pricing per hour
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_sensor_type CHECK (sensor_type IN ('ultrasonic', 'magnetic', 'camera', 'infrared')),
    CONSTRAINT chk_hourly_rate CHECK (hourly_rate >= 0)
);

-- Sensor Data Table (for historical data and analytics)
CREATE TABLE sensor_data (
    id SERIAL PRIMARY KEY,
    sensor_id VARCHAR(50) REFERENCES parking_spots(id) ON DELETE CASCADE,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    occupied BOOLEAN NOT NULL,
    distance_cm DECIMAL(6,2),    -- For ultrasonic sensors
    magnetic_field DECIMAL(8,2), -- For magnetic sensors
    battery_level INTEGER,       -- Battery percentage (0-100)
    signal_strength INTEGER,     -- Wi-Fi signal strength in dBm
    temperature DECIMAL(5,2),    -- Sensor temperature
    humidity DECIMAL(5,2),       -- Sensor humidity
    firmware_version VARCHAR(20),
    raw_data JSONB,              -- Store complete sensor payload
    
    -- Constraints
    CONSTRAINT chk_battery_level CHECK (battery_level >= 0 AND battery_level <= 100),
    CONSTRAINT chk_signal_strength CHECK (signal_strength >= -100 AND signal_strength <= 0)
);

-- Reservations Table
CREATE TABLE reservations (
    id VARCHAR(50) PRIMARY KEY,  -- e.g., RES_1703520000_001
    spot_id VARCHAR(50) REFERENCES parking_spots(id) ON DELETE CASCADE,
    user_email VARCHAR(100) NOT NULL,
    user_phone VARCHAR(20),
    user_name VARCHAR(100),
    start_time TIMESTAMP WITH TIME ZONE NOT NULL,
    end_time TIMESTAMP WITH TIME ZONE NOT NULL,
    duration_hours DECIMAL(4,2) NOT NULL,
    total_amount DECIMAL(8,2) NOT NULL,
    payment_status VARCHAR(20) DEFAULT 'pending',  -- pending, paid, failed, refunded
    payment_intent_id VARCHAR(100),  -- Stripe payment intent ID
    payment_method VARCHAR(50),      -- card, paypal, etc.
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, cancelled, expired
    check_in_time TIMESTAMP WITH TIME ZONE,
    check_out_time TIMESTAMP WITH TIME ZONE,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_payment_status CHECK (payment_status IN ('pending', 'paid', 'failed', 'refunded')),
    CONSTRAINT chk_reservation_status CHECK (status IN ('active', 'completed', 'cancelled', 'expired')),
    CONSTRAINT chk_time_order CHECK (end_time > start_time),
    CONSTRAINT chk_duration CHECK (duration_hours > 0),
    CONSTRAINT chk_amount CHECK (total_amount >= 0)
);

-- Payment Transactions Table
CREATE TABLE payment_transactions (
    id SERIAL PRIMARY KEY,
    reservation_id VARCHAR(50) REFERENCES reservations(id) ON DELETE CASCADE,
    transaction_id VARCHAR(100) UNIQUE NOT NULL,  -- External payment ID
    amount DECIMAL(8,2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    payment_method VARCHAR(50),
    status VARCHAR(20) NOT NULL,  -- pending, completed, failed, refunded
    gateway VARCHAR(20) NOT NULL, -- stripe, paypal, etc.
    gateway_response JSONB,       -- Store complete gateway response
    processed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT chk_payment_status CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    CONSTRAINT chk_amount_positive CHECK (amount > 0)
);

-- System Events Table (for audit trail and monitoring)
CREATE TABLE system_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,  -- sensor_update, reservation_created, payment_completed, etc.
    entity_type VARCHAR(50),          -- spot, reservation, payment, sensor
    entity_id VARCHAR(50),
    user_id VARCHAR(100),             -- Email or user identifier
    event_data JSONB,                 -- Store event details
    ip_address INET,
    user_agent TEXT,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Index for efficient querying
    INDEX idx_system_events_type_time (event_type, timestamp),
    INDEX idx_system_events_entity (entity_type, entity_id)
);

-- Sensor Health Table (for monitoring sensor status)
CREATE TABLE sensor_health (
    sensor_id VARCHAR(50) PRIMARY KEY REFERENCES parking_spots(id) ON DELETE CASCADE,
    last_heartbeat TIMESTAMP WITH TIME ZONE,
    last_data_received TIMESTAMP WITH TIME ZONE,
    battery_level INTEGER,
    signal_strength INTEGER,
    firmware_version VARCHAR(20),
    error_count INTEGER DEFAULT 0,
    last_error TEXT,
    last_error_time TIMESTAMP WITH TIME ZONE,
    is_online BOOLEAN DEFAULT TRUE,
    maintenance_mode BOOLEAN DEFAULT FALSE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Analytics Tables

-- Daily Occupancy Statistics
CREATE TABLE daily_occupancy_stats (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    level VARCHAR(20),
    zone VARCHAR(20),
    total_spots INTEGER NOT NULL,
    peak_occupancy INTEGER NOT NULL,
    avg_occupancy DECIMAL(5,2) NOT NULL,
    occupancy_rate DECIMAL(5,2) NOT NULL,  -- Percentage
    total_revenue DECIMAL(10,2) DEFAULT 0,
    total_reservations INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint to prevent duplicates
    UNIQUE(date, level, zone)
);

-- Hourly Occupancy Statistics
CREATE TABLE hourly_occupancy_stats (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMP WITH TIME ZONE NOT NULL,
    level VARCHAR(20),
    zone VARCHAR(20),
    occupied_spots INTEGER NOT NULL,
    total_spots INTEGER NOT NULL,
    occupancy_rate DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Unique constraint and index
    UNIQUE(datetime, level, zone),
    INDEX idx_hourly_stats_datetime (datetime)
);

-- Create Indexes for Performance

-- Sensor data indexes
CREATE INDEX idx_sensor_data_sensor_time ON sensor_data(sensor_id, timestamp DESC);
CREATE INDEX idx_sensor_data_timestamp ON sensor_data(timestamp DESC);
CREATE INDEX idx_sensor_data_occupied ON sensor_data(occupied, timestamp DESC);

-- Parking spots indexes
CREATE INDEX idx_parking_spots_status ON parking_spots(is_occupied, is_reserved);
CREATE INDEX idx_parking_spots_level_zone ON parking_spots(level, zone);
CREATE INDEX idx_parking_spots_updated ON parking_spots(last_updated DESC);

-- Reservations indexes
CREATE INDEX idx_reservations_spot_time ON reservations(spot_id, start_time, end_time);
CREATE INDEX idx_reservations_user ON reservations(user_email, created_at DESC);
CREATE INDEX idx_reservations_status ON reservations(status, payment_status);
CREATE INDEX idx_reservations_time_range ON reservations(start_time, end_time);

-- Payment transactions indexes
CREATE INDEX idx_payment_transactions_reservation ON payment_transactions(reservation_id);
CREATE INDEX idx_payment_transactions_status ON payment_transactions(status, created_at DESC);

-- Create Views for Common Queries

-- Current Parking Status View
CREATE VIEW current_parking_status AS
SELECT 
    ps.id,
    ps.location,
    ps.level,
    ps.zone,
    ps.spot_number,
    ps.is_occupied,
    ps.is_reserved,
    ps.is_disabled,
    ps.sensor_type,
    ps.hourly_rate,
    ps.last_updated,
    CASE 
        WHEN ps.is_disabled THEN 'disabled'
        WHEN ps.is_occupied THEN 'occupied'
        WHEN ps.is_reserved THEN 'reserved'
        ELSE 'available'
    END as status,
    sh.is_online as sensor_online,
    sh.battery_level,
    sh.signal_strength
FROM parking_spots ps
LEFT JOIN sensor_health sh ON ps.id = sh.sensor_id;

-- Active Reservations View
CREATE VIEW active_reservations AS
SELECT 
    r.*,
    ps.location,
    ps.level,
    ps.zone,
    ps.spot_number
FROM reservations r
JOIN parking_spots ps ON r.spot_id = ps.id
WHERE r.status = 'active' 
  AND r.start_time <= CURRENT_TIMESTAMP 
  AND r.end_time >= CURRENT_TIMESTAMP;

-- Revenue Summary View
CREATE VIEW revenue_summary AS
SELECT 
    DATE(r.created_at) as date,
    COUNT(*) as total_reservations,
    SUM(r.total_amount) as total_revenue,
    AVG(r.total_amount) as avg_reservation_amount,
    AVG(r.duration_hours) as avg_duration_hours
FROM reservations r
WHERE r.payment_status = 'paid'
GROUP BY DATE(r.created_at)
ORDER BY date DESC;

-- Functions and Triggers

-- Function to update parking spot status based on sensor data
CREATE OR REPLACE FUNCTION update_spot_from_sensor()
RETURNS TRIGGER AS $$
BEGIN
    -- Update parking spot status
    UPDATE parking_spots 
    SET 
        is_occupied = NEW.occupied,
        last_updated = NEW.timestamp
    WHERE id = NEW.sensor_id;
    
    -- Update sensor health
    INSERT INTO sensor_health (sensor_id, last_data_received, battery_level, signal_strength, updated_at)
    VALUES (NEW.sensor_id, NEW.timestamp, NEW.battery_level, NEW.signal_strength, CURRENT_TIMESTAMP)
    ON CONFLICT (sensor_id) 
    DO UPDATE SET
        last_data_received = NEW.timestamp,
        battery_level = COALESCE(NEW.battery_level, sensor_health.battery_level),
        signal_strength = COALESCE(NEW.signal_strength, sensor_health.signal_strength),
        updated_at = CURRENT_TIMESTAMP;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger to automatically update spot status when sensor data is inserted
CREATE TRIGGER trigger_update_spot_from_sensor
    AFTER INSERT ON sensor_data
    FOR EACH ROW
    EXECUTE FUNCTION update_spot_from_sensor();

-- Function to automatically expire reservations
CREATE OR REPLACE FUNCTION expire_old_reservations()
RETURNS INTEGER AS $$
DECLARE
    expired_count INTEGER;
BEGIN
    -- Update expired reservations
    UPDATE reservations 
    SET status = 'expired'
    WHERE status = 'active' 
      AND end_time < CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    GET DIAGNOSTICS expired_count = ROW_COUNT;
    
    -- Free up reserved spots for expired reservations
    UPDATE parking_spots 
    SET is_reserved = FALSE
    WHERE id IN (
        SELECT spot_id FROM reservations 
        WHERE status = 'expired' AND is_reserved = TRUE
    );
    
    RETURN expired_count;
END;
$$ LANGUAGE plpgsql;

-- Insert Sample Data

-- Sample parking spots
INSERT INTO parking_spots (id, location, level, zone, spot_number, sensor_type, hourly_rate) VALUES
('PARK_001', 'Level 1 - Zone A - Spot 1', 'L1', 'A', 1, 'ultrasonic', 2.00),
('PARK_002', 'Level 1 - Zone A - Spot 2', 'L1', 'A', 2, 'ultrasonic', 2.00),
('PARK_003', 'Level 1 - Zone A - Spot 3', 'L1', 'A', 3, 'magnetic', 2.00),
('PARK_004', 'Level 1 - Zone B - Spot 1', 'L1', 'B', 1, 'ultrasonic', 2.50),
('PARK_005', 'Level 1 - Zone B - Spot 2', 'L1', 'B', 2, 'camera', 2.50),
('PARK_006', 'Level 2 - Zone A - Spot 1', 'L2', 'A', 1, 'ultrasonic', 1.50),
('PARK_007', 'Level 2 - Zone A - Spot 2', 'L2', 'A', 2, 'ultrasonic', 1.50),
('PARK_008', 'Level 2 - Zone A - Spot 3', 'L2', 'A', 3, 'magnetic', 1.50),
('PARK_009', 'Basement - Zone A - Spot 1', 'B1', 'A', 1, 'infrared', 1.00),
('PARK_010', 'Basement - Zone A - Spot 2', 'B1', 'A', 2, 'ultrasonic', 1.00);

-- Sample sensor health data
INSERT INTO sensor_health (sensor_id, last_heartbeat, last_data_received, battery_level, signal_strength, firmware_version, is_online) VALUES
('PARK_001', CURRENT_TIMESTAMP - INTERVAL '30 seconds', CURRENT_TIMESTAMP - INTERVAL '1 minute', 85, -45, '1.0.0', TRUE),
('PARK_002', CURRENT_TIMESTAMP - INTERVAL '45 seconds', CURRENT_TIMESTAMP - INTERVAL '2 minutes', 92, -38, '1.0.0', TRUE),
('PARK_003', CURRENT_TIMESTAMP - INTERVAL '1 minute', CURRENT_TIMESTAMP - INTERVAL '3 minutes', 78, -52, '1.0.0', TRUE),
('PARK_004', CURRENT_TIMESTAMP - INTERVAL '20 seconds', CURRENT_TIMESTAMP - INTERVAL '30 seconds', 95, -35, '1.0.0', TRUE),
('PARK_005', CURRENT_TIMESTAMP - INTERVAL '2 minutes', CURRENT_TIMESTAMP - INTERVAL '5 minutes', 67, -58, '1.0.0', FALSE);

-- Sample sensor data (recent readings)
INSERT INTO sensor_data (sensor_id, timestamp, occupied, distance_cm, battery_level, signal_strength) VALUES
('PARK_001', CURRENT_TIMESTAMP - INTERVAL '1 minute', FALSE, 250.5, 85, -45),
('PARK_001', CURRENT_TIMESTAMP - INTERVAL '31 minutes', TRUE, 45.2, 85, -45),
('PARK_002', CURRENT_TIMESTAMP - INTERVAL '2 minutes', FALSE, 280.1, 92, -38),
('PARK_003', CURRENT_TIMESTAMP - INTERVAL '3 minutes', TRUE, NULL, 78, -52),  -- Magnetic sensor
('PARK_004', CURRENT_TIMESTAMP - INTERVAL '30 seconds', FALSE, 195.8, 95, -35),
('PARK_005', CURRENT_TIMESTAMP - INTERVAL '5 minutes', TRUE, NULL, 67, -58);  -- Camera sensor

-- Sample reservations
INSERT INTO reservations (id, spot_id, user_email, user_phone, user_name, start_time, end_time, duration_hours, total_amount, payment_status, status) VALUES
('RES_001', 'PARK_002', 'john.doe@example.com', '+1234567890', 'John Doe', 
 CURRENT_TIMESTAMP + INTERVAL '1 hour', CURRENT_TIMESTAMP + INTERVAL '3 hours', 2.0, 4.00, 'paid', 'active'),
('RES_002', 'PARK_004', 'jane.smith@example.com', '+1987654321', 'Jane Smith', 
 CURRENT_TIMESTAMP + INTERVAL '2 hours', CURRENT_TIMESTAMP + INTERVAL '4 hours', 2.0, 5.00, 'pending', 'active');

-- Create a function to generate sample historical data
CREATE OR REPLACE FUNCTION generate_sample_historical_data()
RETURNS VOID AS $$
DECLARE
    spot_record RECORD;
    day_offset INTEGER;
    hour_offset INTEGER;
    random_occupied BOOLEAN;
BEGIN
    -- Generate historical sensor data for the past 7 days
    FOR spot_record IN SELECT id FROM parking_spots LOOP
        FOR day_offset IN 1..7 LOOP
            FOR hour_offset IN 0..23 LOOP
                -- Random occupancy (roughly 60% chance of being occupied during business hours)
                IF hour_offset BETWEEN 8 AND 18 THEN
                    random_occupied := (RANDOM() < 0.6);
                ELSE
                    random_occupied := (RANDOM() < 0.3);
                END IF;
                
                INSERT INTO sensor_data (sensor_id, timestamp, occupied, distance_cm, battery_level, signal_strength)
                VALUES (
                    spot_record.id,
                    CURRENT_TIMESTAMP - INTERVAL '1 day' * day_offset + INTERVAL '1 hour' * hour_offset,
                    random_occupied,
                    CASE WHEN random_occupied THEN 50 + RANDOM() * 100 ELSE 200 + RANDOM() * 100 END,
                    80 + RANDOM() * 20,  -- Battery between 80-100%
                    -60 + RANDOM() * 20  -- Signal strength between -60 to -40 dBm
                );
            END LOOP;
        END LOOP;
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- Uncomment the following line to generate sample historical data
-- SELECT generate_sample_historical_data();

-- Grant permissions to application user
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO parking_user;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO parking_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO parking_user;
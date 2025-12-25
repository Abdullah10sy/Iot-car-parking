# IoT Smart Parking System - Deployment Guide

## Overview

This guide provides comprehensive instructions for deploying the IoT Smart Parking System in various environments, from development to production.

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Hardware      │    │   Edge/Cloud     │    │   User          │
│   Layer         │    │   Processing     │    │   Interface     │
├─────────────────┤    ├──────────────────┤    ├─────────────────┤
│ • ESP32 Sensors │───▶│ • MQTT Broker    │───▶│ • Web Dashboard │
│ • Ultrasonic    │    │ • Backend API    │    │ • Mobile App    │
│ • Magnetic      │    │ • PostgreSQL     │    │ • Admin Panel   │
│ • Camera-based  │    │ • Redis Cache    │    │ • Analytics     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Prerequisites

### System Requirements

**Minimum Requirements:**
- CPU: 2 cores, 2.4 GHz
- RAM: 4 GB
- Storage: 20 GB SSD
- Network: 100 Mbps

**Recommended Requirements:**
- CPU: 4 cores, 3.0 GHz
- RAM: 8 GB
- Storage: 50 GB SSD
- Network: 1 Gbps

### Software Dependencies

**Backend:**
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- MQTT Broker (Mosquitto)

**Frontend:**
- Node.js 16+
- npm 8+

**Hardware:**
- ESP32/NodeMCU development boards
- HC-SR04 ultrasonic sensors
- Jumper wires and breadboards

## Deployment Options

### 1. Local Development Setup

#### Quick Start with Docker Compose

```bash
# Clone the repository
git clone https://github.com/your-org/smart-parking-system.git
cd smart-parking-system

# Copy environment configuration
cp deployment/.env.example .env
# Edit .env with your configuration

# Start all services
docker-compose -f deployment/docker-compose.yml up -d

# Initialize database
docker-compose exec backend python manage.py init-db

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:5000
# MQTT Broker: localhost:1883
```

#### Manual Setup

**1. Setup Database**
```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE parking_db;
CREATE USER parking_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE parking_db TO parking_user;
\q

# Initialize schema
psql -U parking_user -d parking_db -f database/schema.sql
```

**2. Setup Redis**
```bash
# Install Redis
sudo apt-get install redis-server

# Configure Redis (optional)
sudo nano /etc/redis/redis.conf
# Set: requirepass your_redis_password

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

**3. Setup MQTT Broker**
```bash
# Install Mosquitto
sudo apt-get install mosquitto mosquitto-clients

# Configure authentication
sudo mosquitto_passwd -c /etc/mosquitto/passwd parking_system

# Configure Mosquitto
sudo nano /etc/mosquitto/mosquitto.conf
# Add:
# allow_anonymous false
# password_file /etc/mosquitto/passwd

# Start Mosquitto
sudo systemctl start mosquitto
sudo systemctl enable mosquitto
```

**4. Setup Backend**
```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings

# Initialize database
python manage.py init-db

# Start backend services
python app.py &
python mqtt_subscriber.py &
```

**5. Setup Frontend**
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local with your settings

# Start development server
npm run dev
```

### 2. Production Deployment

#### Cloud Deployment (AWS/GCP/Azure)

**Infrastructure Setup:**
```bash
# Using Terraform (example for AWS)
cd deployment/terraform/aws

# Initialize Terraform
terraform init

# Plan deployment
terraform plan -var-file="production.tfvars"

# Deploy infrastructure
terraform apply -var-file="production.tfvars"
```

**Application Deployment:**
```bash
# Build and push Docker images
docker build -t your-registry/parking-backend:latest backend/
docker build -t your-registry/parking-frontend:latest frontend/

docker push your-registry/parking-backend:latest
docker push your-registry/parking-frontend:latest

# Deploy using Kubernetes
kubectl apply -f deployment/kubernetes/
```

#### On-Premises Deployment

**1. Server Setup**
```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

**2. SSL/TLS Setup**
```bash
# Install Certbot for Let's Encrypt
sudo apt-get install certbot

# Generate SSL certificates
sudo certbot certonly --standalone -d your-domain.com

# Configure Nginx with SSL
sudo cp deployment/nginx/nginx-ssl.conf /etc/nginx/sites-available/parking-system
sudo ln -s /etc/nginx/sites-available/parking-system /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

**3. Production Configuration**
```bash
# Copy production environment
cp deployment/.env.production .env

# Edit production settings
nano .env
# Update:
# - Database credentials
# - Redis password
# - MQTT credentials
# - Stripe keys
# - Domain names
# - SSL certificates

# Deploy with production compose file
docker-compose -f deployment/docker-compose.prod.yml up -d
```

### 3. Hardware Deployment

#### ESP32 Sensor Setup

**1. Hardware Assembly**
```
ESP32 Pinout:
- GPIO 5  → HC-SR04 Trigger
- GPIO 18 → HC-SR04 Echo
- 3.3V    → HC-SR04 VCC
- GND     → HC-SR04 GND
- GPIO 2  → Status LED
```

**2. Firmware Installation**
```bash
# Install Arduino IDE and ESP32 board package
# Install required libraries:
# - WiFi
# - PubSubClient (MQTT)
# - ArduinoJson

# Configure sensor settings
cp hardware/esp32_ultrasonic/config.h.example hardware/esp32_ultrasonic/config.h

# Edit config.h with:
# - WiFi credentials
# - MQTT broker settings
# - Sensor ID and location

# Flash firmware to ESP32
# Upload hardware/esp32_ultrasonic/esp32_ultrasonic.ino
```

**3. Sensor Calibration**
```bash
# Test sensor connectivity
mosquitto_sub -h your-mqtt-broker -t "parking/sensor/+/status" -u parking_system -P mqtt_password

# Calibrate distance thresholds
# Measure distances with and without vehicles
# Update OCCUPIED_THRESHOLD_CM in config.h

# Test sensor accuracy
python tests/hardware/test_sensor_calibration.py
```

## Configuration

### Environment Variables

**Backend Configuration (.env):**
```bash
# Database
DATABASE_URL=postgresql://parking_user:password@localhost:5432/parking_db

# Redis
REDIS_URL=redis://:password@localhost:6379

# MQTT
MQTT_BROKER_HOST=localhost
MQTT_BROKER_PORT=1883
MQTT_USERNAME=parking_system
MQTT_PASSWORD=mqtt_password

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Stripe
STRIPE_SECRET_KEY=sk_live_your_stripe_secret
STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

**Frontend Configuration (.env.local):**
```bash
VITE_API_BASE_URL=https://api.your-domain.com
VITE_WEBSOCKET_URL=https://api.your-domain.com
VITE_STRIPE_PUBLISHABLE_KEY=pk_live_your_stripe_publishable
```

### Database Configuration

**PostgreSQL Optimization:**
```sql
-- postgresql.conf optimizations
shared_buffers = 256MB
effective_cache_size = 1GB
maintenance_work_mem = 64MB
checkpoint_completion_target = 0.9
wal_buffers = 16MB
default_statistics_target = 100
random_page_cost = 1.1
effective_io_concurrency = 200
```

**Connection Pooling:**
```bash
# Install PgBouncer
sudo apt-get install pgbouncer

# Configure connection pooling
sudo nano /etc/pgbouncer/pgbouncer.ini
# Set appropriate pool sizes and limits
```

### MQTT Broker Configuration

**Mosquitto Configuration:**
```bash
# /etc/mosquitto/mosquitto.conf
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd

# WebSocket support (optional)
listener 9001
protocol websockets

# Logging
log_dest file /var/log/mosquitto/mosquitto.log
log_type error
log_type warning
log_type notice
log_type information

# Persistence
persistence true
persistence_location /var/lib/mosquitto/

# Security
max_connections 1000
max_inflight_messages 100
```

## Monitoring and Maintenance

### Health Checks

**System Health Monitoring:**
```bash
# API health check
curl -f http://localhost:5000/api/health

# Database connectivity
pg_isready -h localhost -p 5432 -U parking_user

# Redis connectivity
redis-cli ping

# MQTT broker status
mosquitto_pub -h localhost -t test -m "health check"
```

### Logging Configuration

**Centralized Logging:**
```yaml
# docker-compose.yml logging configuration
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

**Log Aggregation with ELK Stack:**
```bash
# Deploy ELK stack for log analysis
docker-compose -f deployment/elk-stack.yml up -d

# Configure Filebeat for log shipping
sudo nano /etc/filebeat/filebeat.yml
```

### Backup Strategy

**Database Backup:**
```bash
#!/bin/bash
# backup_database.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups/postgresql"
DB_NAME="parking_db"

# Create backup
pg_dump -U parking_user -h localhost $DB_NAME | gzip > $BACKUP_DIR/parking_db_$DATE.sql.gz

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "parking_db_*.sql.gz" -mtime +30 -delete
```

**Automated Backup with Cron:**
```bash
# Add to crontab
0 2 * * * /path/to/backup_database.sh
```

### Performance Monitoring

**Metrics Collection:**
```bash
# Deploy Prometheus and Grafana
docker-compose -f deployment/monitoring.yml up -d

# Access Grafana dashboard
# http://localhost:3001 (admin/admin_password)
```

**Key Metrics to Monitor:**
- API response times
- Database query performance
- MQTT message throughput
- Sensor connectivity status
- Memory and CPU usage
- Disk space utilization

## Security Considerations

### Network Security

**Firewall Configuration:**
```bash
# Configure UFW firewall
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 1883/tcp  # MQTT
sudo ufw allow 5432/tcp  # PostgreSQL (internal only)
```

**VPN Setup for Sensors:**
```bash
# Install WireGuard for secure sensor communication
sudo apt-get install wireguard

# Generate keys and configure VPN
wg genkey | tee privatekey | wg pubkey > publickey
```

### Application Security

**API Security:**
- JWT token authentication
- Rate limiting (60 requests/minute)
- Input validation and sanitization
- CORS configuration
- SQL injection prevention

**Database Security:**
- Encrypted connections (SSL/TLS)
- Regular security updates
- Principle of least privilege
- Regular backup verification

### Sensor Security

**MQTT Security:**
- Username/password authentication
- TLS encryption
- Client certificates (optional)
- Topic-based access control

## Troubleshooting

### Common Issues

**1. Sensor Connectivity Issues**
```bash
# Check WiFi connection
ping -c 4 8.8.8.8

# Test MQTT connectivity
mosquitto_pub -h mqtt-broker -t test -m "hello" -u username -P password

# Check sensor logs
# Monitor serial output from ESP32
```

**2. Database Connection Issues**
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
psql -U parking_user -h localhost -d parking_db -c "SELECT 1;"

# Check connection limits
SELECT count(*) FROM pg_stat_activity;
```

**3. API Performance Issues**
```bash
# Check API response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/api/spots

# Monitor database queries
SELECT query, calls, total_time, mean_time 
FROM pg_stat_statements 
ORDER BY total_time DESC LIMIT 10;
```

### Log Analysis

**Backend Logs:**
```bash
# View application logs
docker-compose logs -f backend

# Search for errors
grep -i error /var/log/parking/app.log
```

**MQTT Logs:**
```bash
# View MQTT broker logs
sudo tail -f /var/log/mosquitto/mosquitto.log

# Monitor MQTT traffic
mosquitto_sub -h localhost -t "parking/sensor/+/status" -v
```

## Scaling Considerations

### Horizontal Scaling

**Load Balancing:**
```nginx
# Nginx load balancer configuration
upstream backend_servers {
    server backend1:5000;
    server backend2:5000;
    server backend3:5000;
}

server {
    location /api/ {
        proxy_pass http://backend_servers;
    }
}
```

**Database Scaling:**
- Read replicas for analytics queries
- Connection pooling with PgBouncer
- Partitioning for sensor data tables

### Vertical Scaling

**Resource Optimization:**
- Increase server CPU and RAM
- Use SSD storage for database
- Optimize database queries
- Implement caching strategies

## Support and Maintenance

### Regular Maintenance Tasks

**Weekly:**
- Review system logs
- Check sensor connectivity
- Verify backup integrity
- Monitor disk space

**Monthly:**
- Update system packages
- Review security logs
- Analyze performance metrics
- Clean up old data

**Quarterly:**
- Security audit
- Performance optimization
- Capacity planning
- Disaster recovery testing

### Getting Help

**Documentation:**
- API Documentation: `/docs/api`
- Hardware Guide: `/docs/hardware`
- Troubleshooting: `/docs/troubleshooting`

**Support Channels:**
- GitHub Issues: Report bugs and feature requests
- Email Support: support@smartparking.com
- Community Forum: forum.smartparking.com

**Emergency Contacts:**
- System Administrator: admin@smartparking.com
- On-call Engineer: +1-555-PARKING
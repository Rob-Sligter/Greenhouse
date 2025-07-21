# Greenhouse Monitoring System - Docker Setup

This repository contains a complete Docker-based greenhouse monitoring system for Raspberry Pi that includes:

- **InfluxDB**: Time-series database for storing sensor data
- **Grafana**: Visualization dashboard for monitoring greenhouse conditions
- **Sensor Collector**: Python service that reads sensors and stores data in InfluxDB
- **Sensor API**: Flask web service that handles watering commands via webhooks
- **Web Watering Interface**: User-friendly web interface for manual plant watering

## Prerequisites

### 1. Raspberry Pi Configuration

Before installing the greenhouse system, you need to configure your Raspberry Pi properly:

#### Enable Required Interfaces
```bash
# Open Raspberry Pi configuration tool
sudo raspi-config
```

Navigate through the following options:
- **Interface Options** → **I2C** → **Yes** (for ADS1115 moisture sensors)
- **Interface Options** → **SPI** → **Yes** (if using SPI sensors)
- **Interface Options** → **GPIO** → **Yes** (for relay and sensor control)

After making changes, reboot:
```bash
sudo reboot
```

#### Verify I2C Setup
```bash
# Install I2C tools
sudo apt-get update
sudo apt-get install -y i2c-tools

# Check if I2C is working (should show connected devices)
i2cdetect -y 1
```

#### GPIO Pin Configuration
Ensure your hardware is connected to the correct GPIO pins as defined in the code:

| Component | GPIO Pin | Physical Pin | Notes |
|-----------|----------|--------------|-------|
| DHT11 Inside | GPIO 4 | Pin 7 | Temperature/Humidity sensor |
| DHT11 Outside | GPIO 22 | Pin 15 | Temperature/Humidity sensor |
| Light Sensor | GPIO 27 | Pin 13 | Digital light sensor |
| Relay 1 (Plant 1) | GPIO 17 | Pin 11 | Water pump/valve control |
| Relay 2 (Plant 2) | GPIO 18 | Pin 12 | Water pump/valve control |
| ADS1115 SDA | GPIO 2 | Pin 3 | I2C Data (moisture sensors) |
| ADS1115 SCL | GPIO 3 | Pin 5 | I2C Clock (moisture sensors) |

#### User Permissions
```bash
# Add user to required groups
sudo usermod -aG gpio,i2c,spi $USER

# Verify group membership
groups $USER
```

### 2. Docker and Docker Compose Installation
```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER

# Install Docker Compose plugin
sudo apt-get install docker-compose-plugin

# Reboot to apply group changes
sudo reboot
```

### 3. Hardware Setup
Ensure your sensors are properly connected according to the GPIO pin table above:

#### Required Components:
- **DHT11 Temperature/Humidity Sensors** (x2): Indoor and outdoor monitoring
- **ADS1115 16-bit ADC**: For reading analog moisture sensors
- **Moisture Sensors** (x4): Capacitive soil moisture sensors
- **Light Sensor**: Digital light sensor (LDR with comparator)
- **Relay Modules** (x2): 5V relay modules for water pump control
- **Water Pumps/Valves** (x2): 12V water pumps or solenoid valves

#### Wiring Notes:
- Use 3.3V power for sensors (DHT11, light sensor)
- ADS1115 can use either 3.3V or 5V
- Relays typically need 5V power
- Ensure proper grounding for all components
- Use pull-up resistors for DHT11 sensors (4.7kΩ recommended)

## Hardware Testing

Before running the full system, test each component individually:

### Test GPIO and Relays
```bash
# Test relay control manually
python3 -c "
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.OUT)  # Relay 1
GPIO.setup(18, GPIO.OUT)  # Relay 2

# Turn on relay 1 for 2 seconds
GPIO.output(17, GPIO.LOW)  # Active low relay
print('Relay 1 ON')
time.sleep(2)
GPIO.output(17, GPIO.HIGH)
print('Relay 1 OFF')

GPIO.cleanup()
"
```

### Test All Sensors
Create a test script to verify all sensors:
```bash
# Create test script
cat > test_sensors.py << 'EOF'
#!/usr/bin/env python3
import time
import board
import busio
import dht11
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO

print("Testing all greenhouse sensors...")

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(27, GPIO.IN)  # Light sensor

# I2C setup
try:
    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c)
    chan0 = AnalogIn(ads, ADS.P0)
    print("✓ ADS1115 I2C connection successful")
except Exception as e:
    print(f"✗ ADS1115 I2C connection failed: {e}")

# DHT11 setup
dht_inside = dht11.DHT11(pin=4)
dht_outside = dht11.DHT11(pin=22)

# Test sensors
for i in range(5):
    print(f"\n--- Test {i+1}/5 ---")
    
    # Test DHT11 inside
    result = dht_inside.read()
    if result.is_valid():
        print(f"✓ DHT11 Inside: {result.temperature}°C, {result.humidity}%")
    else:
        print("✗ DHT11 Inside: Read failed")
    
    # Test DHT11 outside
    result = dht_outside.read()
    if result.is_valid():
        print(f"✓ DHT11 Outside: {result.temperature}°C, {result.humidity}%")
    else:
        print("✗ DHT11 Outside: Read failed")
    
    # Test light sensor
    light_value = GPIO.input(27)
    print(f"✓ Light Sensor: {'Dark' if light_value == 0 else 'Bright'}")
    
    # Test moisture sensor
    try:
        moisture_raw = chan0.value
        moisture_voltage = chan0.voltage
        print(f"✓ Moisture Sensor: {moisture_raw} ({moisture_voltage:.2f}V)")
    except Exception as e:
        print(f"✗ Moisture Sensor: {e}")
    
    time.sleep(2)

GPIO.cleanup()
print("\nSensor testing complete!")
EOF

# Run the test
python3 test_sensors.py
```

### Power Supply Check
Ensure adequate power supply for all components:
```bash
# Check system power and temperature
vcgencmd measure_temp
vcgencmd measure_volts
vcgencmd get_throttled
# Should return 0x0 (no throttling)
```

## Installation Guide

1. **Clone/copy the project files** to your Raspberry Pi

2. **Start the entire system**:
   ```bash
   docker compose up -d
   ```

3. **Access the services**:
   - **Grafana Dashboard**: http://your-pi-ip:3000 (admin/admin)
   - **InfluxDB**: http://your-pi-ip:8086
   - **Webhook API**: http://your-pi-ip:5000/receive
   - **Manual Watering Web Interface**: http://your-pi-ip:8080

## Project Structure

The greenhouse monitoring system consists of separate containerized services, each with minimal, optimized dependencies:

### Service-Specific Requirements
- **requirements-sensor-collector.txt**: Full sensor stack (InfluxDB, Adafruit libraries, numpy)
- **requirements-sensor-api.txt**: Lightweight Flask API (webhook handling, GPIO control)
- **requirements-web-watering.txt**: Web interface (Flask, GPIO control, templating)

Each Docker service uses only the dependencies it actually needs, resulting in:
- ⚡ Faster builds (2-5x speed improvement)
- 📦 Smaller container images 
- 🔧 Easier maintenance and debugging
- 🛡️ Reduced attack surface
- 🎯 No dependency bloat

### InfluxDB
- **Port**: 8086
- **Database**: sensor_data
- **Admin User**: admin/adminpassword
- **App User**: greenhouse/greenhouse123

### Grafana
- **Port**: 3000
- **Default Login**: admin/admin
- **Pre-configured**: InfluxDB datasource automatically configured

### Sensor Collector
- Reads all sensors every 20 seconds
- Stores data in InfluxDB
- Handles sensor outliers and averaging
- Monitors: temperature, humidity, moisture, light, sun position

### Sensor API
- Flask web server on port 5000
- Receives POST requests to `/receive` endpoint
- Controls watering relays based on webhook data
- Sends push notifications via Pushover

### Web Watering Interface
- User-friendly web interface on port 8080
- Manual control buttons for each plant
- Adjustable watering duration (1-60 seconds)
- Real-time relay status indicators
- Quick duration preset buttons (3s, 5s, 10s, 15s)
- Responsive design for mobile devices

## Configuration

### Environment Variables
You can customize the setup by modifying environment variables in `docker-compose.yml`:

```yaml
environment:
  - INFLUXDB_HOST=influxdb
  - INFLUXDB_PORT=8086
  - INFLUXDB_DATABASE=sensor_data
```

### Webhook Usage
Send POST requests to `http://your-pi-ip:5000/receive` with JSON payload:
```json
{
  "message": "{\"plant1\": 5, \"plant2\": 3}"
}
```
This will water plant 1 for 5 seconds and plant 2 for 3 seconds.

## Data Management

### Viewing Logs
```bash
# View all services
docker compose logs

# View specific service
docker compose logs sensor_collector
docker compose logs sensor_api
docker compose logs grafana
docker compose logs influxdb
```

### Backup Data
```bash
# Backup InfluxDB data
docker exec greenhouse_influxdb influxd backup -portable /backup
docker cp greenhouse_influxdb:/backup ./influxdb_backup

# Backup Grafana dashboards
docker exec greenhouse_grafana tar czf /tmp/grafana_backup.tar.gz /var/lib/grafana
docker cp greenhouse_grafana:/tmp/grafana_backup.tar.gz ./grafana_backup.tar.gz
```

### Restart Services
```bash
# Restart all services
docker compose restart

# Restart specific service
docker compose restart sensor_collector
```

## Troubleshooting

### Raspberry Pi Configuration Issues

#### I2C Not Working
```bash
# Check if I2C is enabled
sudo raspi-config
# Navigate to Interface Options → I2C → Enable

# Verify I2C kernel modules are loaded
lsmod | grep i2c

# Check I2C devices
i2cdetect -y 1
# Should show your ADS1115 at address 0x48 (default)
```

#### GPIO Permission Issues
```bash
# Check if user is in gpio group
groups $USER
# Should show: pi docker gpio i2c spi

# Add to gpio group if missing
sudo usermod -aG gpio $USER
sudo reboot

# Check GPIO permissions
ls -l /dev/gpiomem
# Should show: crw-rw---- 1 root gpio
```

#### DHT11 Sensor Issues
```bash
# Test DHT11 connectivity manually
python3 -c "
import dht11
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BCM)
sensor = dht11.DHT11(pin=4)
result = sensor.read()
if result.is_valid():
    print(f'Temp: {result.temperature}°C, Humidity: {result.humidity}%')
else:
    print('Sensor read failed')
GPIO.cleanup()
"
```

#### ADS1115/Moisture Sensor Issues
```bash
# Check I2C connection
i2cdetect -y 1
# ADS1115 should appear at 0x48

# Test with Python
python3 -c "
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)
print(f'Channel 0: {chan.value} ({chan.voltage:.2f}V)')
"
```

### Check Service Status
```bash
docker compose ps
```

### Sensor Not Found
- Verify hardware connections
- Check GPIO pin assignments in the code
- Ensure I2C is enabled: `sudo raspi-config` → Interface Options → I2C

### Database Connection Issues
- Verify InfluxDB is running: `docker compose logs influxdb`
- Check network connectivity between services

## Customization

### Adding New Sensors
1. Modify `sensor_out.py` to include new sensor readings
2. Update the `read_sensor_data()` function
3. Rebuild the container: `docker compose up --build sensor_collector`

### Changing Sensor Pins
Update GPIO pin assignments in `sensor_out.py` and `sensor_in.py`, then rebuild:
```bash
docker compose up --build
```

### Custom Grafana Dashboards
1. Create dashboards in Grafana UI
2. Export dashboard JSON
3. Add to `grafana/provisioning/dashboards/` folder
4. Restart Grafana service

## Security Notes

- Change default passwords in production
- Consider adding authentication to InfluxDB
- Use environment files for sensitive data
- Implement proper firewall rules

## System Requirements

- Raspberry Pi 3B+ or newer
- At least 2GB RAM recommended
- 16GB+ SD card
- Stable power supply

# Greenhouse Monitoring System - Docker Setup

This repository contains a complete Docker-based greenhouse monitoring system for Raspberry Pi that includes:

- **InfluxDB**: Time-series database for storing sensor data
- **Grafana**: Visualization dashboard for monitoring greenhouse conditions
- **Sensor Collector**: Python service that reads sensors and stores data in InfluxDB
- **Sensor API**: Flask web service that handles watering commands via webhooks
- **Web Watering Interface**: User-friendly web interface for manual plant watering

## Prerequisites

1. **Docker and Docker Compose** installed on your Raspberry Pi
   ```bash
   curl -fsSL https://get.docker.com -o get-docker.sh
   sudo sh get-docker.sh
   sudo usermod -aG docker $USER
   sudo apt-get install docker-compose-plugin
   ```

2. **Hardware Setup**: Ensure your sensors are properly connected:
   - DHT11 temperature/humidity sensors (pins 4 and 22)
   - ADS1115 ADC for moisture sensors (I2C)
   - Light sensor (pin 27)
   - Relay modules (pins 17 and 18)

## Quick Start

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

## Services Overview

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

### Check Service Status
```bash
docker compose ps
```

### GPIO Permission Issues
If you encounter GPIO permission errors, ensure the containers run with `privileged: true` (already configured).

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

import time
import os
from datetime import datetime

# Third-party imports
import numpy as np
import pytz
from influxdb import InfluxDBClient
from astral import LocationInfo
from astral.sun import sun

# Raspberry Pi specific imports
import RPi.GPIO as GPIO
import board
import busio
import dht11
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

print("Imports successful")

# Configuration constants
CITY_NAME = "Toornwerd"
COUNTRY_NAME = "Netherlands"
TIMEZONE = "Europe/Amsterdam"
LATITUDE = 53.3417  # Latitude of Toornwerd
LONGITUDE = 6.4639  # Longitude of Toornwerd

# GPIO pin assignments
LIGHT_PIN = 27
TEMP_HUMI_PIN_INSIDE = 4
TEMP_HUMI_PIN_OUTSIDE = 22

# Moisture sensor calibration values
MIN_VALUES = [8602, 8602, 8602, 8602]
MAX_VALUES = [17590, 17590, 17590, 17590]

# Data collection interval (seconds)
COLLECTION_INTERVAL = 20

# Initialize global variables
plant_1_readings = []
plant_2_readings = []

# GPIO setup
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(LIGHT_PIN, GPIO.IN)

# Initialize I2C and ADS1115
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# Initialize temperature/humidity sensors
temp_humi_sensor_inside = dht11.DHT11(pin=TEMP_HUMI_PIN_INSIDE)
temp_humi_sensor_outside = dht11.DHT11(pin=TEMP_HUMI_PIN_OUTSIDE)

# Initialize InfluxDB client
influxdb_host = os.getenv('INFLUXDB_HOST', 'localhost')
influxdb_port = int(os.getenv('INFLUXDB_PORT', '8086'))
influxdb_database = os.getenv('INFLUXDB_DATABASE', 'sensor_data')
client = InfluxDBClient(host=influxdb_host, port=influxdb_port, database=influxdb_database)

def is_sun_up(city_name, country_name, timezone, latitude, longitude):
    try:
        # Define the location
        location = LocationInfo(city_name, country_name, timezone, latitude, longitude)
        
        # Get the current time in the specified timezone
        tz = pytz.timezone(timezone)
        now = datetime.now(tz)

        # Get today's sunrise and sunset times
        s = sun(location.observer, date=now.date(), tzinfo=tz)

        # Check if the current time is between sunrise and sunset
        if s['sunrise'] <= now <= s['sunset']:
            return 1
        else:
            return 0
    except:
        return 0

def read_dht11_sensor_inside():
    try:
        # Read the humidity and temperature
        result = temp_humi_sensor_inside.read()
        count = 0
        while not result.is_valid() and count < 10:
            result = temp_humi_sensor_inside.read()
            time.sleep(0.1)
            count += 1
        if result.is_valid():
            return round(result.temperature, 1), round(result.humidity, 1)
        else:
            return round(0.0, 1), round(0.0, 1)
    except:
        return round(0.0, 1), round(0.0, 1)

def read_dht11_sensor_outside():
    try:
        # Read the humidity and temperature
        result = temp_humi_sensor_outside.read()
        count = 0
        while not result.is_valid() and count < 10:
            result = temp_humi_sensor_outside.read()
            time.sleep(0.1)
            count += 1
        if result.is_valid():
            return round(result.temperature, 1), round(result.humidity, 1)
        else:
            return round(0.0, 1), round(0.0, 1)
    except:
        return round(0.0, 1), round(0.0, 1)

def read_light_sensor(light_pin):
    try:
        sensor_value = GPIO.input(light_pin)
        if sensor_value == GPIO.HIGH:
            return 0
        else:
            return 1
    except:
        return 0

# Function to detect and remove outliers using IQR
def remove_outliers(data):
    if len(data) < 4:  # Not enough data to calculate IQR
        return data
    q1, q3 = np.percentile(data, [25, 75])
    iqr = q3 - q1
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    return [x for x in data if lower_bound <= x <= upper_bound]

def read_all_channels():
    try:
        global plant_1_readings, plant_2_readings
        if True:
            channels = [chan0, chan1, chan2, chan3]
            current_values = [chan.value for chan in channels]
            
            percentages = []
            for i, value in enumerate(current_values):
                range_value = MAX_VALUES[i] - MIN_VALUES[i]
                if range_value != 0:
                    percentage = ((MAX_VALUES[i] - value) / range_value) * 100
                else:
                    percentage = 0
                percentages.append(percentage)
            
            plant_1 = round(percentages[0], 1)
            plant_2 = round(percentages[-1], 1)
            
            # Update readings lists
            plant_1_readings.append(plant_1)
            plant_2_readings.append(plant_2)
            
            # Keep only the last 8 readings
            if len(plant_1_readings) > 8:
                plant_1_readings.pop(0)
            if len(plant_2_readings) > 8:
                plant_2_readings.pop(0)
            time.sleep(0.1)
        
        # Remove outliers
        filtered_plant_1 = remove_outliers(plant_1_readings)
        filtered_plant_2 = remove_outliers(plant_2_readings)
        
        # Calculate averages
        if filtered_plant_1:
            avg_plant_1 = round(sum(filtered_plant_1) / len(filtered_plant_1), 1)
        else:
            avg_plant_1 = 0

        if filtered_plant_2:
            avg_plant_2 = round(sum(filtered_plant_2) / len(filtered_plant_2), 1)
        else:
            avg_plant_2 = 0

        if avg_plant_1 > 100:
            avg_plant_1 = 100.0 
        elif avg_plant_1 < 0:
            avg_plant_1 = 0.0
        if avg_plant_2 > 100:
            avg_plant_2 = 100.0
        elif avg_plant_2 < 0:
            avg_plant_2 = 0.0

        return avg_plant_1, avg_plant_2
    except:
        return round(1.0, 1), round(1.0, 1)


def read_sensor_data():
    moisture_plant_1, moisture_plant_2 = read_all_channels()
    light = read_light_sensor(LIGHT_PIN)
    temperature_inside, humidity_inside = read_dht11_sensor_inside()
    temperature_outside, humidity_outside = read_dht11_sensor_outside()
    sun_up = is_sun_up(CITY_NAME, COUNTRY_NAME, TIMEZONE, LATITUDE, LONGITUDE)

    return {
        "temperature_inside": temperature_inside,  
        "humidity_inside": humidity_inside,
        "temperature_outside": temperature_outside,  
        "humidity_outside": humidity_outside,
        "light": light,
        "moisture_plant_1":  moisture_plant_1,
        "moisture_plant_2":  moisture_plant_2,
        "sun_up": sun_up
    }

def send_data_to_influx(data):
    json_body = [
        {
            "measurement": "greenhouse_data",
            "tags": {
                "host": "raspberrypi"
            },
            "fields": data
        }
    ]
    client.write_points(json_body)


if __name__ == "__main__":
    print("Starting greenhouse sensor monitoring...")
    
    while True:
        try:
            sensor_data = read_sensor_data()
            print(sensor_data)
            send_data_to_influx(sensor_data)
            time.sleep(COLLECTION_INTERVAL)
        except KeyboardInterrupt:
            print("\nShutting down sensor monitoring...")
            GPIO.cleanup()
            break
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(COLLECTION_INTERVAL)

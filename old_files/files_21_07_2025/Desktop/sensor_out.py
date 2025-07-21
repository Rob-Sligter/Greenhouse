import time
import board
import busio
import dht11
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn
import RPi.GPIO as GPIO
import numpy as np
import os
try:
    from influxdb import InfluxDBClient
except:
    os.system("pip install influxdb")
    from influxdb import InfluxDBClient

try:
    from astral import LocationInfo
    from astral.sun import sun
except ModuleNotFoundError:
    import os
    os.system("pip install astral")
    from astral import LocationInfo
    from astral.sun import sun
from datetime import datetime

try:
    import pytz
except ModuleNotFoundError:
    import os
    os.system("pip install pytz")
    import pytz

print("Imports succesful")

#moisture variables 
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS.ADS1115(i2c)
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)
min_values = [8602, 8602, 8602, 8602]
max_values = [17590, 17590, 17590, 17590]
plant_1_readings = []
plant_2_readings = []

GPIO.setwarnings(False)

#light variables
light_pin_1 = 27  # GPIO pin connected to the sensor OUT
GPIO.setmode(GPIO.BCM)
GPIO.setup(light_pin_1, GPIO.IN)  # No internal pull-up/pull-down

#temp and humi variables
temp_humi_pin_inside = 4  # replace with your GPIO pin number
temp_humi_sensor_inside = dht11.DHT11(pin=temp_humi_pin_inside)
temp_humi_pin_outside = 22  # replace with your GPIO pin number
temp_humi_sensor_outside = dht11.DHT11(pin=temp_humi_pin_outside)
# Create an instance of the InfluxDB client
client = InfluxDBClient(host='localhost', port=8086, database='sensor_data')

#sun_up api
city_name = "Toornwerd"
country_name = "Netherlands"
timezone = "Europe/Amsterdam"  # Toornwerd, Groningen, Netherlands timezone
latitude = 53.3417  # Latitude of Toornwerd
longitude = 6.4639  # Longitude of Toornwerd

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

# Function to read all channels and print percentages
def read_all_channels():
    try:
        global min_values, max_values, plant_1_readings, plant_2_readings
        if True:
            channels = [chan0, chan1, chan2, chan3]
            current_values = [chan.value for chan in channels]
            
            percentages = []
            for i, value in enumerate(current_values):
                range_value = max_values[i] - min_values[i]
                if range_value != 0:
                    percentage = ((max_values[i] - value) / range_value) * 100
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
    global light_pin_1
    moisture_plant_1, moisture_plant_2 = read_all_channels()
    light = read_light_sensor(light_pin_1)
    temperature_inside, humidity_inside = read_dht11_sensor_inside()
    temperature_outside, humidity_outside = read_dht11_sensor_outside()
    sun_up = is_sun_up(city_name, country_name, timezone, latitude, longitude)

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


while True:
    sensor_data = read_sensor_data()
    print(sensor_data)
    send_data_to_influx(sensor_data)
    time.sleep(20)  # wait for 60 seconds before the next read

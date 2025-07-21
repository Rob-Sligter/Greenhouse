import time
import os
try:
    from influxdb import InfluxDBClient
except:
    os.system("pip install influxdb")
    from influxdb import InfluxDBClient

# Create an instance of the InfluxDB client
client = InfluxDBClient(host='localhost', port=8086, database='sensor_data')

def read_sensor_data():
    # Replace this function with the actual method to read from sensors
    return {
        "temperature": 19.1,  # Example temperature data
        "humidity": 50,        # Example humidity data
    }

def send_data_to_influx(data):
    json_body = [
        {
            "measurement": "your_measurement",
            "tags": {
                "host": "raspberrypi"
            },
            "fields": data
        }
    ]
    client.write_points(json_body)

if __name__ == "__main__":
    while True:
        sensor_data = read_sensor_data()
        send_data_to_influx(sensor_data)
        time.sleep(60)  # wait for 60 seconds before the next read

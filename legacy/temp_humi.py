import RPi.GPIO as GPIO
import dht11
import time

# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)  # Use BCM GPIO numbering
GPIO.cleanup()

# Set GPIO pin where the DHT11 is connected
gpio_pin = 4  # replace with your GPIO pin number

# Initialize the DHT11 sensor
sensor = dht11.DHT11(pin=gpio_pin)

def read_dht11_sensor():
    # Read the humidity and temperature
    result = sensor.read()
    # Check if the reading is successful
    if result.is_valid():
        print(f'Temperature: {result.temperature:.1f}°C')
        print(f'Humidity: {result.humidity:.1f}%')
    else:
        print('Failed to get reading. Try again!')

if __name__ == "__main__":
    try:
        while True:
            read_dht11_sensor()
            time.sleep(2)  # wait for 2 seconds before the next reading
    except KeyboardInterrupt:
        print("Program stopped by User")
        GPIO.cleanup()

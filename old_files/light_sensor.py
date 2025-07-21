import RPi.GPIO as GPIO
import time

# Pin Definitions
light_pin = 27  # GPIO pin connected to the sensor OUT

# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setup(light_pin, GPIO.IN)  # No internal pull-up/pull-down

try:
    while True:
        # Read sensor value
        sensor_value = GPIO.input(light_pin)
        if sensor_value == GPIO.HIGH:
            print(False)
        else:
            print(True)
        time.sleep(1)
except KeyboardInterrupt:
    pass
finally:
    GPIO.cleanup()

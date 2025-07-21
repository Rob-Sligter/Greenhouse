import RPi.GPIO as GPIO
import time

# Set the GPIO pin number where the relay is connected
RELAY_PIN = 17  # You can change this to the pin you are using
ACTIVE_LOW = True  # Set to False if your relay is active high

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN, GPIO.OUT)

# Function to flip the relay
def flip_relay():
    # Determine the state to turn the relay on and off
    relay_on = GPIO.LOW if ACTIVE_LOW else GPIO.HIGH
    relay_off = GPIO.HIGH if ACTIVE_LOW else GPIO.LOW

    try:
        # Turn on the relay
        print("Turning relay ON")
        GPIO.output(RELAY_PIN, relay_on)
        print("Relay should be ON now")
        time.sleep(2)  # Keep the relay on for 2 seconds

        # Turn off the relay
        print("Turning relay OFF")
        GPIO.output(RELAY_PIN, relay_off)
        print("Relay should be OFF now")
        time.sleep(2)  # Keep the relay off for 2 seconds

    except KeyboardInterrupt:
        print("Program interrupted")
    finally:
        print("Cleaning up GPIO")
        GPIO.cleanup()

if __name__ == "__main__":
    try:
        while True:
            flip_relay()
    except KeyboardInterrupt:
        print("Program terminated by user")
    finally:
        GPIO.cleanup()
        print("GPIO cleanup complete")

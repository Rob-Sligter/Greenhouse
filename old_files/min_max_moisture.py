import time
import board
import busio
import adafruit_ads1x15.ads1115 as ADS
from adafruit_ads1x15.analog_in import AnalogIn

# Create the I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create the ADS object
ads = ADS.ADS1115(i2c)

# Create single-ended input on each channel
chan0 = AnalogIn(ads, ADS.P0)
chan1 = AnalogIn(ads, ADS.P1)
chan2 = AnalogIn(ads, ADS.P2)
chan3 = AnalogIn(ads, ADS.P3)

# Initialize min and max values
min_values = [float('inf')] * 4
max_values = [float('-inf')] * 4

# Function to read all channels and update min/max values
def read_all_channels():
    global min_values, max_values
    
    channels = [chan0, chan1, chan2, chan3]
    current_values = [chan.value for chan in channels]
    
    for i, value in enumerate(current_values):
        if value < min_values[i]:
            min_values[i] = value
        if value > max_values[i]:
            max_values[i] = value
    
    print(f"Current values: {current_values}")
    print(f"Min values: {min_values}")
    print(f"Max values: {max_values}")

# Main loop
try:
    while True:
        read_all_channels()
        time.sleep(0.1) 
except KeyboardInterrupt:
    print("Program stopped by User")

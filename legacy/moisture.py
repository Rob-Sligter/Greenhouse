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
min_values = [25758, 940, 939, 25977]
max_values = [28598, 10742, 9808, 28641]

# Function to read all channels and print percentages
def read_all_channels():
    global min_values, max_values
    
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
    return plant_1, plant_2

# Main loop
try:
    while True:
        print(read_all_channels())
        time.sleep(0.1) 
except KeyboardInterrupt:
    print("Program stopped by User")

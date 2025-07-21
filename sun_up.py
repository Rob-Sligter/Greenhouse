try:
    from astral import LocationInfo
    from astral.sun import sun
except ModuleNotFoundError:
    import os
    os.system("pip install astral")
    from astral import LocationInfo
    from astral.sun import sun

from datetime import datetime
import time
try:
    import pytz
except ModuleNotFoundError:
    import os
    os.system("pip install pytz")
    import pytz

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

# Example usage for Toornwerd, Groningen, Netherlands
city_name = "Toornwerd"
country_name = "Netherlands"
timezone = "Europe/Amsterdam"  # Toornwerd, Groningen, Netherlands timezone
latitude = 53.3417  # Latitude of Toornwerd
longitude = 6.4639  # Longitude of Toornwerd


while 1:
    if is_sun_up(city_name, country_name, timezone, latitude, longitude):
        print("The sun is up in Toornwerd, Groningen, Netherlands.")
    else:
        print("The sun is down in Toornwerd, Groningen, Netherlands.")
    time.sleep(10*60)
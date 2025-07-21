from flask import Flask, render_template, request, jsonify, redirect, url_for
import RPi.GPIO as GPIO
import time
import threading
import os
import http.client
import urllib.parse

app = Flask(__name__)

# GPIO Configuration
RELAY_PIN_1 = 17  
RELAY_PIN_2 = 18  
ACTIVE_LOW = True  

# Set up the GPIO mode
GPIO.setmode(GPIO.BCM)
GPIO.setup(RELAY_PIN_1, GPIO.OUT)
GPIO.setup(RELAY_PIN_2, GPIO.OUT)

relay_on = GPIO.LOW if ACTIVE_LOW else GPIO.HIGH
relay_off = GPIO.HIGH if ACTIVE_LOW else GPIO.LOW
GPIO.output(RELAY_PIN_1, relay_off)
GPIO.output(RELAY_PIN_2, relay_off)

def send_push_message(push_notification):
    """Send push notification via Pushover"""
    try:
        conn = http.client.HTTPSConnection("api.pushover.net:443")
        conn.request("POST", "/1/messages.json",
        urllib.parse.urlencode({
            "token": "aa66iazeqbepcsjmf6x8rmf5cgh9yc",
            "user": "uqwnoar4qmhr7j99mvczdu7ob2edkd",
            "message": push_notification,
        }), { "Content-type": "application/x-www-form-urlencoded" })
        conn.getresponse()
    except Exception as e:
        print(f"Failed to send push notification: {e}")

def water_plant_async(plant_number, duration):
    """Water plant asynchronously to avoid blocking the web interface"""
    def water():
        try:
            relay_pin = RELAY_PIN_1 if plant_number == 1 else RELAY_PIN_2
            print(f"Watering plant {plant_number} for {duration} seconds...")
            
            GPIO.output(relay_pin, relay_on)
            time.sleep(duration)
            GPIO.output(relay_pin, relay_off)
            
            send_push_message(f"Plant {plant_number} manually watered for {duration} seconds")
            print(f"Plant {plant_number} watering complete")
        except Exception as e:
            print(f"Error watering plant {plant_number}: {e}")
    
    # Start watering in a separate thread
    thread = threading.Thread(target=water)
    thread.daemon = True
    thread.start()

@app.route('/')
def index():
    """Main page with watering controls"""
    return render_template('index.html')

@app.route('/water', methods=['POST'])
def water():
    """Handle watering requests"""
    try:
        plant_number = int(request.form.get('plant'))
        duration = int(request.form.get('duration', 5))
        
        if plant_number not in [1, 2]:
            return jsonify({"error": "Invalid plant number"}), 400
        
        if duration < 1 or duration > 60:
            return jsonify({"error": "Duration must be between 1 and 60 seconds"}), 400
        
        water_plant_async(plant_number, duration)
        
        return jsonify({
            "success": True, 
            "message": f"Plant {plant_number} is being watered for {duration} seconds"
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/status')
def status():
    """Get current GPIO status"""
    try:
        plant1_status = "ON" if GPIO.input(RELAY_PIN_1) == relay_on else "OFF"
        plant2_status = "ON" if GPIO.input(RELAY_PIN_2) == relay_on else "OFF"
        
        return jsonify({
            "plant1": plant1_status,
            "plant2": plant2_status
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

def cleanup():
    """Cleanup GPIO on exit"""
    GPIO.cleanup()

if __name__ == '__main__':
    try:
        print("Starting Greenhouse Manual Watering Web Server...")
        print("Access the web interface at: http://your-pi-ip:8080")
        app.run(host='0.0.0.0', port=8080, debug=False)
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        cleanup()

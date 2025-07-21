from flask import Flask, request, jsonify
import json
import RPi.GPIO as GPIO
import time
import http.client, urllib

def send_push_message(push_notification):
    conn = http.client.HTTPSConnection("api.pushover.net:443")
    conn.request("POST", "/1/messages.json",
    urllib.parse.urlencode({
        "token": "aa66iazeqbepcsjmf6x8rmf5cgh9yc",
        "user": "uqwnoar4qmhr7j99mvczdu7ob2edkd",
        "message": push_notification,
    }), { "Content-type": "application/x-www-form-urlencoded" })
    conn.getresponse()




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

def flip_relay(number: int, seconds: int):
    if number == 1: 
        relay_pin = 17
    else:
        relay_pin  = 18
    relay_on = GPIO.LOW if ACTIVE_LOW else GPIO.HIGH
    relay_off = GPIO.HIGH if ACTIVE_LOW else GPIO.LOW
    try:
        GPIO.output(relay_pin, relay_on)
        time.sleep(seconds)  
        GPIO.output(relay_pin, relay_off)
        send_push_message(f"Plant {number} watered for {seconds} seconds")
    except KeyboardInterrupt:
        print("Program interrupted")
    

app = Flask(__name__)

@app.route('/receive', methods=['POST'])
def webhook():
    data = request.get_json()  # Assuming the payload is JSON
    if data and 'message' in data:
        message = data['message']
        message = json.loads(message)
        # Extract the number from the message assuming the format "{water: 3}"
        try:
            for plant in message:
                flip_relay(number=int(str(plant)[-1]), seconds=int(message[plant]))
            return jsonify({"status": "success"}), 200
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 400
    return jsonify({"status": "error", "message": "Invalid data"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

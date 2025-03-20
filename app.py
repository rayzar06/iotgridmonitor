from flask import Flask, render_template, flash
import firebase_admin
from firebase_admin import credentials, db
from twilio.rest import Client  # Import Twilio client
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Initialize Firebase
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://smart-energy-meter-9469c-default-rtdb.asia-southeast1.firebasedatabase.app'
})

# Twilio Credentials (Replace with your Twilio credentials)
TWILIO_ACCOUNT_SID = "AC4741ab9f2012ef763817901cce4e80b2"
TWILIO_AUTH_TOKEN = "7697165c5af2c62213275a2b3e84d2bb"
TWILIO_PHONE_NUMBER = "+19204889655"  # Replace with your Twilio phone number
RECIPIENT_PHONE_NUMBER = "+919567039990"  # Replace with the phone number to receive alerts

# Overload Parameters
THRESHOLD_CURRENT = 5  # Overload threshold in Amperes
SAFETY_MARGIN = 0      # Allow minor fluctuations

# Helper function to format timestamp
def format_timestamp(timestamp):
    return datetime.fromtimestamp(int(timestamp)).strftime('%Y-%m-%d %H:%M:%S')

# Function to send SMS alert
def send_sms_alert(message):
    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=RECIPIENT_PHONE_NUMBER
        )
        print("SMS alert sent successfully!")
    except Exception as e:
        print(f"Error sending SMS: {str(e)}")

# Function to detect overload and send an SMS alert
def detect_overload():
    try:
        ref = db.reference('UsersData/f85kQS2SPNa635nGzPqV7w709Bs1/readings')
        data = ref.get()

        if data:
            for key, value in data.items():
                current = float(value['current'])
                if current > (THRESHOLD_CURRENT + SAFETY_MARGIN):
                    alert_message = f"⚠️ Overload Alert! Detected at {format_timestamp(value['timestamp'])}"
                    send_sms_alert(alert_message)
                    flash(alert_message, "danger")
                    return True  # Overload detected
        return False  # No overload
    except Exception as e:
        flash(f"Error detecting overload: {str(e)}", "danger")
        return False

@app.route('/')
def index():
    detect_overload()  # Check for overload on page load

    # Fetch historical data
    try:
        ref = db.reference('UsersData/f85kQS2SPNa635nGzPqV7w709Bs1/readings')
        data = ref.get()

        readings = []
        if data:
            for key, value in data.items():
                value['id'] = key
                value['timestamp'] = format_timestamp(value['timestamp'])
                readings.append(value)

        readings = readings[-10:]  # Limit to last 10 readings
    except Exception as e:
        flash(f"Error fetching data: {str(e)}", "danger")
        readings = []

    return render_template('index.html', readings=readings)

if __name__ == '__main__':
    app.run(debug=True)

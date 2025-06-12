''' 
 Nama File      : app.py
 Tanggal Update : 09 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
   1. Program baca data dari MQTT broker, 
      kemudian tampilkan pada halaman web dashboard,
      dengan beberapa fitur seperti: 
        - Tampilan data real-time
        - Tampilan data historis
        - Tampilan data prediksi
    2. Program ini juga menyediakan halaman engineer untuk
        - Melihat data historis
        - Melihat data prediksi
        - Mengunduh data historis dalam format Excel
    3. Program ini menggunakan Flask sebagai web framework,
        Dash untuk visualisasi data, 
        dan Paho MQTT untuk komunikasi dengan broker MQTT.
    4. Program ini juga menggunakan Google Sheets untuk menyimpan data historis
        dan mengunduhnya dalam format Excel. 
    5. Program ini juga menyediakan halaman login untuk engineer
    6. Program ini juga menyediakan halaman GPS untuk melihat lokasi perangkat
    7. Program ini juga menyediakan halaman alarm untuk melihat status alarm
    8. Program ini juga menyediakan halaman CO2, T&H Indoor, T&H Outdoor, PAR, Windspeed, Rainfall
    9. Program ini juga menyediakan halaman multipage untuk engineer
    10. Program ini juga menyediakan halaman multipage untuk guest    
'''

# Deklarasi library yang digunakan
from flask import Flask, render_template, redirect, url_for, request, flash, session, send_file
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import dash
import dash_bootstrap_components as dbc
import secrets
import paho.mqtt.client as mqtt
import plotly.graph_objects as go
import threading
import ssl
import pytz
import random
import pandas as pd
import numpy as np
from scipy import interpolate
from datetime import datetime, timedelta
from dash import dcc, html
from dash.dependencies import Input, Output
from pages.mcs_dashboard_all import main_dashboard_layout, main_dashboard_path
from pages.co2 import co2_layout
from pages.th_in import th_in_layout
from pages.th_out import th_out_layout  
from pages.par import par_layout    
from pages.windspeed import windspeed_layout    
from pages.rainfall import rainfall_layout  
from pages.alarm import alarm_layout  
from pages.gps import gps_layout  
from engineer_pages.mcs_dashboard_eng import engineer_dashboard_layout
from engineer_pages.co2_eng import engineer_co2_layout
from engineer_pages.th_in_eng import engineer_th_in_layout
from engineer_pages.th_out_eng import engineer_th_out_layout  
from engineer_pages.par_eng import engineer_par_layout    
from engineer_pages.windspeed_eng import engineer_windspeed_layout    
from engineer_pages.rainfall_eng import engineer_rainfall_layout  
from engineer_pages.alarm_eng import engineer_alarm_layout  
from engineer_pages.gps_eng import engineer_gps_layout  
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import gspread                               
from oauth2client.service_account import ServiceAccountCredentials 
import io                                    

# Load environment variables
load_dotenv()

# Initialize Flask app
server = Flask(__name__)

# UPDATED: Secure secret key from environment
server.secret_key = os.getenv('SECRET_KEY', '9f9f9f9f9f9f9f9f9f9f9f9f9f9f9')  # Use a strong secret key

# Menyimpan daftar halaman multipage
pages = {
    main_dashboard_path: main_dashboard_layout,
    "/dash/co2": co2_layout,
    "/dash/th-in": th_in_layout,
    "/dash/th-out": th_out_layout,
    "/dash/par": par_layout,
    "/dash/windspeed": windspeed_layout,
    "/dash/rainfall": rainfall_layout,
    "/dash/alarm": alarm_layout,
    "/dash/gps": gps_layout,
}

engineer_pages = {
    "/dash/engineer/": engineer_dashboard_layout,
    "/dash/engineer/co2": engineer_co2_layout,
    "/dash/engineer/th-in": engineer_th_in_layout,
    "/dash/engineer/th-out": engineer_th_out_layout,
    "/dash/engineer/par": engineer_par_layout,
    "/dash/engineer/windspeed": engineer_windspeed_layout,
    "/dash/engineer/rainfall": engineer_rainfall_layout,
    "/dash/engineer/alarm": engineer_alarm_layout,
    "/dash/engineer/gps": engineer_gps_layout,
}

# Configure Flask-Login
login_manager = LoginManager()
login_manager.init_app(server)
login_manager.login_view = 'login'  # Specify the login route

# UPDATED: Secure user data with hashed passwords
users = {
    'engineer': {
        'password_hash': generate_password_hash(os.getenv('ENGINEER_PASSWORD', 'password'))
    }
}

class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Flask routes
@server.route('/')
def home():
    # Public home page, redirects to guest dashboard
    return redirect('/dash/')

# UPDATED: Secure login route with password hashing
@server.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        # Input validation
        if not username or not password:
            flash('Username and password are required')
            return redirect(url_for('login'))
        
        # Check if user exists and password is correct
        if username in users and check_password_hash(users[username]['password_hash'], password):
            user = User(username)
            login_user(user)
            return redirect(url_for('dashboard'))
        
        flash('Invalid credentials')
        return redirect(url_for('login'))

    return render_template('login.html')

@server.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', user=current_user.id)

# NEW FLASK ROUTE FOR DOWNLOADING THE SPREADSHEET
@server.route('/download')
def download_spreadsheet():
    try:
        # 1. Authenticate with Google Sheets using the service account
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and get all data from the first sheet
        #    Replace "microclimate_database" with the exact name of your Google Sheet file
        sheet = client.open("microclimate_database").sheet1
        data = sheet.get_all_records()  # This gets data as a list of dictionaries

        # 3. Convert data to a Pandas DataFrame
        df = pd.DataFrame(data)

        # 4. Create an in-memory Excel file from the DataFrame
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='SensorData')
        output.seek(0) # Move the cursor to the beginning of the stream

        # 5. Send the file to the user's browser for download
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'microclimate_data_{datetime.now().strftime("%Y-%m-%d")}.xlsx'
        )

    except gspread.exceptions.SpreadsheetNotFound:
        return "Error: Spreadsheet not found. Check the name or sharing permissions.", 404
    except Exception as e:
        print(f"An error occurred during file download: {e}")
        return "An internal error occurred. Please check the server logs.", 500

@server.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')  # Redirect to public home page
# end of flask route

# Integrate Dash app
app_dash = dash.Dash(__name__, server=server, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.BOOTSTRAP], title='MCS Dashboard', suppress_callback_exceptions=True, assets_folder='assets', update_title=False)
 
@app_dash.server.before_request
def restrict_dash_pages():
    if request.path.startswith('/dash/engineer') and not session.get('_user_id'):
        return redirect(url_for('login'))

# NEW: Connection monitoring variables
connection_status = {
    'connected': False,
    'last_message_time': None,
    'connection_timeout': 80  # seconds - consider disconnected if no message for 60 seconds
}

# NEW: Default values for sensors
DEFAULT_VALUES = {
    'kodeData0000': "-",  # Cycle start signal
    'kodeData0211': "-",
    'kodeData0212': "-",
    'kodeData0711': "-",
    'kodeData0712': "-",
    'kodeData0311': "-",
    'kodeData0411': "-",
    'kodeData0511': "-",
    'kodeData0611': "-",
    'kodeData1011': "-",
    'kodeData1012': "-",
    'kodeData0911': "-",
    'kodeData0912': "-",
    'kodeData0913': "-",
}

# Default values for alarms
DEFAULT_ALARM_VALUES = {
    'kodeAlarm0211': 5,
    'kodeAlarm0212': 5,
    'kodeAlarm0711': 5,
    'kodeAlarm0712': 5,
    'kodeAlarm0311': 5,
    'kodeAlarm0411': 5,
    'kodeAlarm0511': 5,
    'kodeAlarm0611': 5,
    'kodeAlarm0911': 5,
    'kodeAlarm0912': 5,
    'kodeAlarm0913': 5,
    'berita0211': 'N/A',
    'berita0212': 'N/A',
    'berita0711': 'N/A',
    'berita0712': 'N/A',
    'berita0311': 'N/A',
    'berita0411': 'N/A',
    'berita0511': 'N/A',
    'berita0611': 'N/A',
    'berita0911': 'N/A',
    'berita0912': 'N/A',
    'berita0913': 'N/A',
}

# Default values for predicitons
DEFAULT_PREDICTION_VALUES = {
    'kodeData0213': "-",
    'kodeData0214': "-",
    'kodeData0215': "-",
    'kodeData0216': "-",
    'kodeData0217': "-",
    'kodeData0218': "-",
    'kodeData0219': "-",
    'kodeData0220': "-",
    'kodeData0221': "-",
    'kodeData0222': "-",
    'kodeData0713': "-",
    'kodeData0714': "-",
    'kodeData0715': "-",
    'kodeData0716': "-",
    'kodeData0717': "-",
    'kodeData0718': "-",
    'kodeData0719': "-",
    'kodeData0720': "-",
    'kodeData0721': "-",
    'kodeData0722': "-",
    'kodeData0312': "-",
    'kodeData0313': "-",
    'kodeData0314': "-",
    'kodeData0315': "-",
    'kodeData0316': "-",
    'kodeData0412': "-",
    'kodeData0413': "-",
    'kodeData0414': "-",
    'kodeData0415': "-",
    'kodeData0416': "-",
    'kodeData0512': "-",
    'kodeData0513': "-",
    'kodeData0514': "-",
    'kodeData0515': "-",
    'kodeData0516': "-",
    'kodeData0612': "-",
    'kodeData0613': "-",
    'kodeData0614': "-",
    'kodeData0615': "-",
    'kodeData0616': "-",
}

# data storage
data = {
    'waktu': [],      # Time values
    'kodeData0000': [],  # Cycle start signal
    'kodeData0211': [],       # Temperature values 
    'kodeData0212': [], # Humidity values
    'kodeData0711': [],   # Outdoor temperature values
    'kodeData0712': [], # Outdoor humidity values
    'kodeData0311': [],        # CO2 values
    'kodeData0411': [],  # Wind speed values
    'kodeData0511': [],    # Rainfall values
    'kodeData0611': [],    # PAR values
    'kodeData1011': [],   # Latitude values
    'kodeData1012': [],    # Longitude values
    'kodeData0911': [], # Voltage AC values
    'kodeData0912': [], # Current AC values
    'kodeData0913': [], # Power AC values
}

# Alarm data storage
alarm_data = {
    'kodeAlarm0211': 5,
    'kodeAlarm0212': 5,
    'kodeAlarm0711': 5,
    'kodeAlarm0712': 5,
    'kodeAlarm0311': 5,
    'kodeAlarm0411': 5,
    'kodeAlarm0511': 5,
    'kodeAlarm0611': 5,
    'kodeAlarm0911': 5,
    'kodeAlarm0912': 5,
    'kodeAlarm0913': 5,
    'berita0211': 'N/A',
    'berita0212': 'N/A',
    'berita0711': 'N/A',
    'berita0712': 'N/A',
    'berita0311': 'N/A',
    'berita0411': 'N/A',
    'berita0511': 'N/A',
    'berita0611': 'N/A',
    'berita0911': 'N/A',
    'berita0912': 'N/A',
    'berita0913': 'N/A',
}

# Prediction data storage
prediction_data = {
    'kodeData0213': [],
    'kodeData0214': [],
    'kodeData0215': [],
    'kodeData0216': [],
    'kodeData0217': [],
    'kodeData0218': [],
    'kodeData0219': [],
    'kodeData0220': [],
    'kodeData0221': [],
    'kodeData0222': [],
    'kodeData0713': [],
    'kodeData0714': [],
    'kodeData0715': [],
    'kodeData0716': [],
    'kodeData0717': [],
    'kodeData0718': [],
    'kodeData0719': [],
    'kodeData0720': [],
    'kodeData0721': [],
    'kodeData0722': [],
    'kodeData0312': [],
    'kodeData0313': [],
    'kodeData0314': [],
    'kodeData0315': [],
    'kodeData0316': [],
    'kodeData0412': [],
    'kodeData0413': [],
    'kodeData0414': [],
    'kodeData0415': [],
    'kodeData0416': [],
    'kodeData0512': [],
    'kodeData0513': [],
    'kodeData0514': [],
    'kodeData0515': [],
    'kodeData0516': [],
    'kodeData0612': [],
    'kodeData0613': [],
    'kodeData0614': [],
    'kodeData0615': [],
    'kodeData0616': [],
}

# Helper function for safe numeric conversion
def safe_float_convert(value, default_display="N/A"):
    """
    Safely convert a value to float with proper formatting.
    Returns formatted string or default_display if conversion fails.
    """
    try:
        # Handle None values
        if value is None:
            return default_display
        
        # Handle string values
        if isinstance(value, str):
            # Check if it's a default placeholder
            if value == "-" or value.strip() == "":
                return default_display
            # Try to convert string to float
            return f"{float(value):.1f}"
        
        # Handle numeric values (int, float)
        if isinstance(value, (int, float)):
            return f"{float(value):.1f}"
        
        # If it's any other type, return default
        return default_display
        
    except (ValueError, TypeError):
        return default_display

# Define some locations in Bandung, Indonesia for demonstration
LOCATIONS = [
    {"name": "Bandung City Square", "lat": -6.921151, "lon": 107.607301},
    {"name": "Gedung Sate", "lat": -6.902454, "lon": 107.618881},
    {"name": "Dago Street", "lat": -6.893702, "lon": 107.613251},
    {"name": "Bandung Station", "lat": -6.914744, "lon": 107.602458},
    {"name": "Paris Van Java Mall", "lat": -6.888771, "lon": 107.595337}
]

# Coordinates for a device path simulation
def generate_path_points(center_lat, center_lon, points=10, radius=0.005):
    """Generate a path of points around a center location"""
    path = []
    for i in range(points):
        # Create a small random deviation
        lat_offset = radius * np.cos(i * 2 * np.pi / points)
        lon_offset = radius * np.sin(i * 2 * np.pi / points)
        
        # Add small random noise
        lat_noise = random.uniform(-0.0005, 0.0005)
        lon_noise = random.uniform(-0.0005, 0.0005)
        
        path.append({
            "lat": center_lat + lat_offset + lat_noise,
            "lon": center_lon + lon_offset + lon_noise
        })
    return path

# Generate a sample path
PATH_POINTS = generate_path_points(-6.914744, 107.609810, points=20)

# UPDATED: MQTT Configuration from environment variables
BROKER = os.getenv('MQTT_BROKER', "broker")
PORT = int(os.getenv('MQTT_PORT', 'port'))
USERNAME = os.getenv('MQTT_USERNAME', "username")
PASSWORD = os.getenv('MQTT_PASSWORD', "password")
MQTT_VERIFY_CERTS = os.getenv('MQTT_VERIFY_CERTS', 'true').lower() == 'true'

# UPDATED: Secure SSL context creation
def create_secure_ssl_context():
    """Create SSL context with proper security"""
    ssl_context = ssl.create_default_context()
    
    # Only disable verification if explicitly set to false (for development only)
    if not MQTT_VERIFY_CERTS:
        print("WARNING: MQTT certificate verification disabled - not recommended for production!")
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    
    return ssl_context

# Create SSL context
ssl_context = create_secure_ssl_context()

# MQTT topics
TOPIC_CYCLE_START = "mcs/kodeData0000"  # Topic for cycle start signal

# TOPIC FOR DATA
TOPIC_SUHU = "mcs/kodeData0211"
TOPIC_KELEMBABAN = "mcs/kodeData0212"
TOPIC_SUHU_OUT = "mcs/kodeData0711"
TOPIC_KELEMBABAN_OUT = "mcs/kodeData0712"
TOPIC_CO2 = "mcs/kodeData0311"
TOPIC_WINDSPEED = "mcs/kodeData0411"
TOPIC_RAINFALL = "mcs/kodeData0511"
TOPIC_PAR = "mcs/kodeData0611"
TOPIC_LAT = "mcs/kodeData1011"
TOPIC_LON = "mcs/kodeData1012"
TOPIC_VOLTAGE_AC = "mcs/kodeData0911"
TOPIC_CURRENT_AC = "mcs/kodeData0912"
TOPIC_POWER_AC = "mcs/kodeData0913"

# TOPIC FOR ALARM
TOPIC_ALARM_SUHU_IN = "mcs/kodeAlarm0211"
TOPIC_ALARM_KELEMBABAN_IN = "mcs/kodeAlarm0212"
TOPIC_ALARM_SUHU_OUT = "mcs/kodeAlarm0711"
TOPIC_ALARM_KELEMBABAN_OUT = "mcs/kodeAlarm0712"
TOPIC_ALARM_CO2 = "mcs/kodeAlarm0311"
TOPIC_ALARM_WINDSPEED = "mcs/kodeAlarm0411"
TOPIC_ALARM_RAINFALL = "mcs/kodeAlarm0511"
TOPIC_ALARM_PAR = "mcs/kodeAlarm0611"
TOPIC_ALARM_VOLTAGE_AC = "mcs/kodeAlarm0911"
TOPIC_ALARM_CURRENT_AC = "mcs/kodeAlarm0912"
TOPIC_ALARM_POWER_AC = "mcs/kodeAlarm0913"

# TOPIC FOR BERITA
TOPIC_BERITA_SUHU_IN = "mcs/berita0211"
TOPIC_BERITA_KELEMBABAN_IN = "mcs/berita0212"
TOPIC_BERITA_SUHU_OUT = "mcs/berita0711"
TOPIC_BERITA_KELEMBABAN_OUT = "mcs/berita0712"
TOPIC_BERITA_CO2 = "mcs/berita0311"
TOPIC_BERITA_WINDSPEED = "mcs/berita0411"
TOPIC_BERITA_RAINFALL = "mcs/berita0511"
TOPIC_BERITA_PAR = "mcs/berita0611"
TOPIC_BERITA_VOLTAGE_AC = "mcs/berita0911"
TOPIC_BERITA_CURRENT_AC = "mcs/berita0912"
TOPIC_BERITA_POWER_AC = "mcs/berita0913"

# TOPIC FOR PREDICTION
TOPIC_SUHU_PREDICT1 = "mcs/kodeData0213"
TOPIC_SUHU_PREDICT2 = "mcs/kodeData0214"
TOPIC_SUHU_PREDICT3 = "mcs/kodeData0215"
TOPIC_SUHU_PREDICT4 = "mcs/kodeData0216"
TOPIC_SUHU_PREDICT5 = "mcs/kodeData0217"
TOPIC_HUMIDITY_PREDICT1 = "mcs/kodeData0218"
TOPIC_HUMIDITY_PREDICT2 = "mcs/kodeData0219"
TOPIC_HUMIDITY_PREDICT3 = "mcs/kodeData0220"
TOPIC_HUMIDITY_PREDICT4 = "mcs/kodeData0221"
TOPIC_HUMIDITY_PREDICT5 = "mcs/kodeData0222"
TOPIC_SUHUOUT_PREDICT1 = "mcs/kodeData0713"
TOPIC_SUHUOUT_PREDICT2 = "mcs/kodeData0714"
TOPIC_SUHUOUT_PREDICT3 = "mcs/kodeData0715"
TOPIC_SUHUOUT_PREDICT4 = "mcs/kodeData0716"
TOPIC_SUHUOUT_PREDICT5 = "mcs/kodeData0717"
TOPIC_HUMIDITYOUT_PREDICT1 = "mcs/kodeData0718"
TOPIC_HUMIDITYOUT_PREDICT2 = "mcs/kodeData0719"
TOPIC_HUMIDITYOUT_PREDICT3 = "mcs/kodeData0720"
TOPIC_HUMIDITYOUT_PREDICT4 = "mcs/kodeData0721"
TOPIC_HUMIDITYOUT_PREDICT5 = "mcs/kodeData0722"
TOPIC_CO2_PREDICT1 = "mcs/kodeData0312"
TOPIC_CO2_PREDICT2 = "mcs/kodeData0313"
TOPIC_CO2_PREDICT3 = "mcs/kodeData0314"
TOPIC_CO2_PREDICT4 = "mcs/kodeData0315"
TOPIC_CO2_PREDICT5 = "mcs/kodeData0316"
TOPIC_WINDSPEED_PREDICT1 = "mcs/kodeData0412"
TOPIC_WINDSPEED_PREDICT2 = "mcs/kodeData0413"
TOPIC_WINDSPEED_PREDICT3 = "mcs/kodeData0414"
TOPIC_WINDSPEED_PREDICT4 = "mcs/kodeData0415"
TOPIC_WINDSPEED_PREDICT5 = "mcs/kodeData0416"
TOPIC_RAINFALL_PREDICT1 = "mcs/kodeData0512"
TOPIC_RAINFALL_PREDICT2 = "mcs/kodeData0513"
TOPIC_RAINFALL_PREDICT3 = "mcs/kodeData0514"
TOPIC_RAINFALL_PREDICT4 = "mcs/kodeData0515"
TOPIC_RAINFALL_PREDICT5 = "mcs/kodeData0516"
TOPIC_PAR_PREDICT1 = "mcs/kodeData0612"
TOPIC_PAR_PREDICT2 = "mcs/kodeData0613"
TOPIC_PAR_PREDICT3 = "mcs/kodeData0614"
TOPIC_PAR_PREDICT4 = "mcs/kodeData0615"
TOPIC_PAR_PREDICT5 = "mcs/kodeData0616"

# NEW: Function to check if data is stale
def is_data_stale():
    """Check if the last received data is older than the timeout period"""
    if connection_status['last_message_time'] is None:
        return True
    
    time_diff = datetime.now() - connection_status['last_message_time']
    return time_diff.total_seconds() > connection_status['connection_timeout']

# NEW: Function to reset data to defaults
def reset_to_default_values():
    """Reset all sensor data to default values"""
    global data
    global alarm_data
    global prediction_data
    current_time = datetime.now(tz=pytz.timezone('Asia/Jakarta')).strftime('%H:%M:%S')
    
    # Clear existing data and add default values
    for key in DEFAULT_VALUES:
        data[key] = [DEFAULT_VALUES[key]]

    # Clear existing alarm_data and add default_alarm_values
    for key2 in DEFAULT_ALARM_VALUES:
        alarm_data[key2] = [DEFAULT_ALARM_VALUES[key2]]

    # Clear existing prediction_data and add default_prediction_values
    for key3 in DEFAULT_PREDICTION_VALUES:
        prediction_data[key3] = [DEFAULT_PREDICTION_VALUES[key3]] 
    
    data['waktu'] = [current_time]
    print("Data reset to default values due to connection timeout")

# MQTT Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ Broker")
        client.subscribe([(TOPIC_CYCLE_START, 0),
                          (TOPIC_SUHU, 0), (TOPIC_KELEMBABAN, 0),
                          (TOPIC_SUHU_OUT, 0), (TOPIC_KELEMBABAN_OUT, 0),
                          (TOPIC_CO2, 0), (TOPIC_WINDSPEED, 0), 
                          (TOPIC_RAINFALL, 0), (TOPIC_PAR, 0),
                          (TOPIC_LAT, 0),  (TOPIC_LON, 0),
                          (TOPIC_VOLTAGE_AC, 0), (TOPIC_CURRENT_AC, 0), (TOPIC_POWER_AC, 0),
                          (TOPIC_ALARM_SUHU_IN, 0), (TOPIC_ALARM_KELEMBABAN_IN, 0),
                          (TOPIC_ALARM_SUHU_OUT, 0), (TOPIC_ALARM_KELEMBABAN_OUT, 0),
                          (TOPIC_ALARM_CO2, 0), (TOPIC_ALARM_WINDSPEED, 0),
                          (TOPIC_ALARM_RAINFALL, 0), (TOPIC_ALARM_PAR, 0),
                          (TOPIC_ALARM_VOLTAGE_AC, 0), (TOPIC_ALARM_CURRENT_AC, 0),
                          (TOPIC_ALARM_POWER_AC, 0), (TOPIC_BERITA_VOLTAGE_AC, 0),
                          (TOPIC_BERITA_CURRENT_AC, 0), (TOPIC_BERITA_POWER_AC, 0),
                          (TOPIC_BERITA_SUHU_IN, 0), (TOPIC_BERITA_KELEMBABAN_IN, 0),
                          (TOPIC_BERITA_SUHU_OUT, 0), (TOPIC_BERITA_KELEMBABAN_OUT, 0),
                          (TOPIC_BERITA_CO2, 0), (TOPIC_BERITA_WINDSPEED, 0),
                          (TOPIC_BERITA_RAINFALL, 0), (TOPIC_BERITA_PAR, 0),
                          (TOPIC_SUHU_PREDICT1, 0), (TOPIC_SUHU_PREDICT2, 0),
                          (TOPIC_SUHU_PREDICT3, 0), (TOPIC_SUHU_PREDICT4, 0),
                          (TOPIC_SUHU_PREDICT5, 0), (TOPIC_HUMIDITY_PREDICT1, 0),
                          (TOPIC_HUMIDITY_PREDICT2, 0), (TOPIC_HUMIDITY_PREDICT3, 0),
                          (TOPIC_HUMIDITY_PREDICT4, 0), (TOPIC_HUMIDITY_PREDICT5, 0),
                          (TOPIC_SUHUOUT_PREDICT1, 0), (TOPIC_SUHUOUT_PREDICT2, 0),
                          (TOPIC_SUHUOUT_PREDICT3, 0), (TOPIC_SUHUOUT_PREDICT4, 0),
                          (TOPIC_SUHUOUT_PREDICT5, 0), (TOPIC_HUMIDITYOUT_PREDICT1, 0),
                          (TOPIC_HUMIDITYOUT_PREDICT2, 0), (TOPIC_HUMIDITYOUT_PREDICT3, 0),
                          (TOPIC_HUMIDITYOUT_PREDICT4, 0), (TOPIC_HUMIDITYOUT_PREDICT5, 0),
                          (TOPIC_CO2_PREDICT1, 0), (TOPIC_CO2_PREDICT2, 0),
                          (TOPIC_CO2_PREDICT3, 0), (TOPIC_CO2_PREDICT4, 0),
                          (TOPIC_CO2_PREDICT5, 0), (TOPIC_PAR_PREDICT1, 0),
                          (TOPIC_PAR_PREDICT2, 0), (TOPIC_PAR_PREDICT3, 0),
                          (TOPIC_PAR_PREDICT4, 0), (TOPIC_PAR_PREDICT5, 0),
                          (TOPIC_WINDSPEED_PREDICT1, 0), (TOPIC_WINDSPEED_PREDICT2, 0),
                          (TOPIC_WINDSPEED_PREDICT3, 0), (TOPIC_WINDSPEED_PREDICT4, 0),
                          (TOPIC_WINDSPEED_PREDICT5, 0), (TOPIC_RAINFALL_PREDICT1, 0),
                          (TOPIC_RAINFALL_PREDICT2, 0), (TOPIC_RAINFALL_PREDICT3, 0),
                          (TOPIC_RAINFALL_PREDICT4, 0), (TOPIC_RAINFALL_PREDICT5, 0)                                                           
                          ])  # Subscribe ke topik suhu & kelembaban
    else:
        print(f"Failed to connect, return code {rc}")

# NEW: Enhanced on_disconnect callback
def on_disconnect(client, userdata, rc):
    global connection_status
    connection_status['connected'] = False
    if rc != 0:
        print(f"Unexpected MQTT disconnection. Return code: {rc}")
        print("Attempting to reconnect...")
        # Attempt to reconnect
        try:
            client.reconnect()
        except Exception as e:
            print(f"Reconnection failed: {e}")

def on_message(client, userdata, msg):
    global data, alarm_data, connection_status, prediction_data
    try:
        # Update connection status
        connection_status['last_message_time'] = datetime.now()
        connection_status['connected'] = True
        
        topic = msg.topic.split('/')[-1]  # Get the last part of the topic

        # Define a consistent history length
        MAX_HISTORY = 10

        # List of topics that appear in the real-time table
        table_data_topics = [
            'kodeData0211', 'kodeData0212', 'kodeData0711', 'kodeData0712',
            'kodeData0311', 'kodeData0411', 'kodeData0511', 'kodeData0611',
            'kodeData1011', 'kodeData1012', 'kodeData0911', 'kodeData0912', 
            'kodeData0913'
        ]

        # Topics to round to 2 decimal places
        topics_to_round = [
            'kodeData0211', 'kodeData0212', 'kodeData0711', 'kodeData0712',
            'kodeData0311', 'kodeData0411', 'kodeData0511', 'kodeData0611',
            'kodeData0911', 'kodeData0912', 'kodeData0913'
        ]
        
        # Process regular data topics
        if topic == 'kodeData0000':
            raw_payload = float(msg.payload.decode())
            payload = round(raw_payload, 2) if topic in topics_to_round else raw_payload
            
            current_time = datetime.now(tz=pytz.timezone('Asia/Jakarta')).strftime('%H:%M:%S')
            data['waktu'].append(current_time)
            data[topic].append(payload) # Use the potentially rounded payload

            for key in table_data_topics:
                last_value = data[key][-1] if data[key] else None
                data[key].append(last_value)

        # Other data topics: These UPDATE the last row
        elif topic in table_data_topics:
            raw_payload = float(msg.payload.decode())
            payload = round(raw_payload, 2) if topic in topics_to_round else raw_payload
            
            if data[topic]:
                data[topic][-1] = payload # Use the rounded payload
        
        # Process alarm code topics
        elif topic.startswith('kodeAlarm'):
            try:
                alarm_value = int(msg.payload.decode())
                alarm_data[topic] = alarm_value
                print(f"Updated alarm {topic}: {alarm_value}")
            except ValueError:
                print(f"Error parsing alarm value for {topic}: {msg.payload.decode()}")
        
        # Process berita (alert message) topics
        elif topic.startswith('berita'):
            berita_value = msg.payload.decode()
            alarm_data[topic] = berita_value
            print(f"Updated berita {topic}: {berita_value}")

        # Process prediction data topics
        elif  topic in ['kodeData0213', 'kodeData0214', 'kodeData0215', 'kodeData0216',
                    'kodeData0217', 'kodeData0218', 'kodeData0219', 'kodeData0220',
                    'kodeData0221', 'kodeData0222', 'kodeData0713', 'kodeData0714', 
                    'kodeData0715', 'kodeData0716', 'kodeData0717', 'kodeData0718',
                    'kodeData0719', 'kodeData0720', 'kodeData0721', 'kodeData0722',
                    'kodeData0312', 'kodeData0313', 'kodeData0314', 'kodeData0315',
                    'kodeData0316', 'kodeData0412', 'kodeData0413', 'kodeData0414',
                    'kodeData0415', 'kodeData0416', 'kodeData0512', 'kodeData0513',
                    'kodeData0514', 'kodeData0515', 'kodeData0516', 'kodeData0612',
                    'kodeData0613', 'kodeData0614', 'kodeData0615', 'kodeData0616']:
            # Process prediction values
            try:
                predict_value = float(msg.payload.decode())
                prediction_data[topic].append(predict_value)
                print(f"Updated prediction {topic}: {predict_value}")
            except ValueError:
                print(f"Error parsing prediction value for {topic}: {msg.payload.decode()}")

        # Trim all historical lists at the end
        for key in data.keys():
            if len(data[key]) > MAX_HISTORY:
                data[key] = data[key][-MAX_HISTORY:]

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# UPDATED: MQTT Client with enhanced reconnection logic
def setup_mqtt_client():
    """Setup MQTT client with proper error handling and reconnection"""
    try:
        client = mqtt.Client()  # Maintain session for better reconnection
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl_context)
        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect
        
        # Set keepalive and other connection parameters
        client.keepalive = 60
        
        # Connect with error handling
        result = client.connect(BROKER, PORT, 60)
        if result == 0:
            print("MQTT client connected successfully")
            return client
        else:
            print(f"Failed to connect to MQTT broker. Return code: {result}")
            return None
            
    except Exception as e:
        print(f"Error setting up MQTT client: {e}")
        return None
    
# NEW: Background thread to monitor connection and reset data if needed
def connection_monitor():
    """Monitor connection status and reset data if no messages received"""
    while True:
        try:
            if is_data_stale():
                if connection_status['connected']:
                    print("No recent data received, connection may be stale")
                    connection_status['connected'] = False
                reset_to_default_values()
            time.sleep(30)  # Check every 30 seconds
        except Exception as e:
            print(f"Error in connection monitor: {e}")
            time.sleep(30)

# NEW: MQTT reconnection thread
def mqtt_reconnection_handler(client):
    """Handle MQTT reconnection in a separate thread"""
    while True:
        try:
            if not connection_status['connected']:
                print("Attempting MQTT reconnection...")
                client.reconnect()
                time.sleep(10)  # Wait before next attempt
            else:
                time.sleep(60)  # Check every minute when connected
        except Exception as e:
            print(f"Reconnection attempt failed: {e}")
            time.sleep(10)

# Initialize MQTT client
mqtt_client = setup_mqtt_client()
if mqtt_client:
    # Run MQTT in thread only if connection successful
    mqtt_thread = threading.Thread(target=mqtt_client.loop_forever, daemon=True)
    mqtt_thread.start()
    
    # Start connection monitor thread
    monitor_thread = threading.Thread(target=connection_monitor, daemon=True)
    monitor_thread.start()
    
    # Start reconnection handler thread  
    reconnect_thread = threading.Thread(target=mqtt_reconnection_handler, args=(mqtt_client,), daemon=True)
    reconnect_thread.start()
    
    print("MQTT client and monitoring threads started")
else:
    print("MQTT client not started due to connection issues")
    # Start monitor thread even without MQTT to reset data
    monitor_thread = threading.Thread(target=connection_monitor, daemon=True)
    monitor_thread.start()

# main layout dash
app_dash.layout = html.Div([
    # CSS styles for the app
    html.Link(rel='stylesheet', href='/static/style.css'),

    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content', children=[]),    
])

# Callback Routing berdasarkan URL
@app_dash.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    # Check if it's an engineer path
    if pathname.startswith('/dash/engineer/'):
        # Verify user is authenticated
        if not current_user.is_authenticated:
            return html.Div([
                html.H3('Access Denied'),
                html.P('Please log in as an engineer to access this page.'),
                html.A('Login', href='/login', className='btn btn-primary')
            ])
        # Show engineer page if authenticated
        if pathname in engineer_pages:
            return engineer_pages[pathname]
        # 404 for invalid engineer paths
        return html.Div([
            html.H3('404: Page not found'),
            html.A('Go to engineer dashboard', href='/dash/engineer/')
        ])
    
    # For guest paths (no authentication needed)
    if pathname in pages:
        return pages[pathname]
    
    # Default to guest homepage for unknown paths
    return pages['/dash/']

# Callback for main dashboard
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'suhu-display-indoor'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'kelembaban-display-indoor'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'suhu-display-outdoor'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'kelembaban-display-outdoor'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'co2-display'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'windspeed-display'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'rainfall-display'}, 'children'),
     Output({'type': 'sensor-value', 'id': 'par-display'}, 'children')],
    [Input('interval_mcs', 'n_intervals')]
)
def update_main_dashboard(n):
    try:
        # Get latest values or default if no data
        suhu = data['kodeData0211'][-1] if data['kodeData0211'] else DEFAULT_VALUES['kodeData0211']
        kelembaban = data['kodeData0212'][-1] if data['kodeData0212'] else DEFAULT_VALUES['kodeData0212']
        suhu_out = data['kodeData0711'][-1] if data['kodeData0711'] else DEFAULT_VALUES['kodeData0711']
        kelembaban_out = data['kodeData0712'][-1] if data['kodeData0712'] else DEFAULT_VALUES['kodeData0712']
        co2 = data['kodeData0311'][-1] if data['kodeData0311'] else DEFAULT_VALUES['kodeData0311']
        windspeed = data['kodeData0411'][-1] if data['kodeData0411'] else DEFAULT_VALUES['kodeData0411']
        rainfall = data['kodeData0511'][-1] if data['kodeData0511'] else DEFAULT_VALUES['kodeData0511']
        par = data['kodeData0611'][-1] if data['kodeData0611'] else DEFAULT_VALUES['kodeData0611']

        return (
            f" {suhu}°C",
            f" {kelembaban}%",
            f" {suhu_out}°C",
            f" {kelembaban_out}%",
            f" {co2}PPM",
            f" {windspeed}m/s",
            f" {rainfall}mm",
            f" {par}μmol/m²/s"
        )
    except Exception as e:
        print(f"Error in update_main_dashboard: {e}")
        return "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A", "N/A"

# Separate callback for th_in layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'suhu-display-indoor'}, 'children', allow_duplicate=True),
     Output({'type': 'sensor-value', 'id': 'kelembaban-display-indoor'}, 'children', allow_duplicate=True),
     Output('temp-graph', 'figure'),
     Output('humidity-graph', 'figure')],
    [Input('interval_thin', 'n_intervals')],
    prevent_initial_call=True
)
def update_th_in_dashboard(n):
    try:        
        # Default values
        suhu_value = "N/A"
        kelembaban_value = "N/A"
        
        # Empty figures with proper layout
        empty_temp_fig = go.Figure(layout=dict(
            title="Temperature Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Temperature (°C)", range=[0, 40]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        empty_humid_fig = go.Figure(layout=dict(
            title="Humidity Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Humidity (%)", range=[0, 100]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0211'] or not data['kodeData0212'] or not data['waktu']:
            return suhu_value, kelembaban_value, empty_temp_fig, empty_humid_fig
        
        # Get the latest values
        suhu = data['kodeData0211'][-1] if data['kodeData0211'] else DEFAULT_VALUES['kodeData0211']
        kelembaban = data['kodeData0212'][-1] if data['kodeData0212'] else DEFAULT_VALUES['kodeData0212']
        suhu_value = f"{suhu}°C"
        kelembaban_value = f"{kelembaban}%"
        
        # Create temperature graph with properly aligned x and y values
        temp_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0211']) > 3:
                # We'll use only 4 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0211']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0211'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                temp_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#FF4B4B', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                temp_fig.update_layout(
                    title="Temperature Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Temperature (°C)", range=[0, 40]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=150,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                temp_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#FF4B4B', width=3),
                    showlegend=False
                ))
                temp_fig.update_layout(
                    title="Temperature Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Temperature (°C)", range=[0, 40]),
                    height=150,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating temp graph: {e}")
            # Create a basic empty chart if there's an error
            temp_fig = go.Figure()
            temp_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        # Create humidity graph with properly aligned x and y values
        humid_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0212']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0212']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0212'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                humid_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                humid_fig.update_layout(
                    title="Humidity Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Humidity (%)", range=[0, 100]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=150,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                humid_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                humid_fig.update_layout(
                    title="Humidity Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Humidity (%)", range=[0, 100]),
                    height=150,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating humid graph: {e}")
            # Create a basic empty chart if there's an error
            humid_fig = go.Figure()
            humid_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        
        return suhu_value, kelembaban_value, temp_fig, humid_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", "N/A", default_fig, default_fig
    
# Separate callback for th_out layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'suhu-display-outdoor'}, 'children', allow_duplicate=True),
     Output({'type': 'sensor-value', 'id': 'kelembaban-display-outdoor'}, 'children', allow_duplicate=True),
     Output('temp-graph-out', 'figure'),
     Output('humidity-graph-out', 'figure')],
    [Input('interval_thout', 'n_intervals')],
    prevent_initial_call=True
)
def update_th_out_dashboard(n):
    try:        
        # Default values
        suhu_value = "N/A"
        kelembaban_value = "N/A"
        
        # Empty figures with proper layout
        empty_temp_fig = go.Figure(layout=dict(
            title="Temperature Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Temperature (°C)", range=[0, 40]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        empty_humid_fig = go.Figure(layout=dict(
            title="Humidity Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Humidity (%)", range=[0, 100]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0711'] or not data['kodeData0712'] or not data['waktu']:
            return suhu_value, kelembaban_value, empty_temp_fig, empty_humid_fig
        
        # Get the latest values
        suhu = data['kodeData0711'][-1] if data['kodeData0711'] else DEFAULT_VALUES['kodeData0711']
        kelembaban = data['kodeData0712'][-1] if data['kodeData0712'] else DEFAULT_VALUES['kodeData0712']
        suhu_value = f"{suhu}°C"
        kelembaban_value = f"{kelembaban}%"

        # Create temperature graph with properly aligned x and y values
        temp_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0711']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0711']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0711'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                temp_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#FF4B4B', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                temp_fig.update_layout(
                    title="Temperature Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Temperature (°C)", range=[0, 40]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=150,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                temp_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#FF4B4B', width=3),
                    showlegend=False
                ))
                temp_fig.update_layout(
                    title="Temperature Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Temperature (°C)", range=[0, 40]),
                    height=150,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating temp graph: {e}")
            # Create a basic empty chart if there's an error
            temp_fig = go.Figure()
            temp_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )

        # Create humidity graph with properly aligned x and y values
        humid_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0712']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0712']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0712'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                humid_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                humid_fig.update_layout(
                    title="Humidity Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Humidity (%)", range=[0, 100]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=150,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                humid_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                humid_fig.update_layout(
                    title="Humidity Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Humidity (%)", range=[0, 100]),
                    height=150,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating humid graph: {e}")
            # Create a basic empty chart if there's an error
            humid_fig = go.Figure()
            humid_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        return suhu_value, kelembaban_value, temp_fig, humid_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", "N/A", default_fig, default_fig
    
# Separate callback for windspeed layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'windspeed-display'}, 'children', allow_duplicate=True),
     Output('windspeed-graph', 'figure')],
    [Input('interval_windspeed', 'n_intervals')],
    prevent_initial_call=True
)
def update_windspeed_dashboard(n):
    try:        
        # Default values
        windspeed_value = "N/A"
        
        # Empty figures with proper layout
        empty_windspeed_fig = go.Figure(layout=dict(
            title="Windspeed Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Windspeed (m/s)", range=[0, 70]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0411'] or not data['waktu']:
            return windspeed_value, empty_windspeed_fig
        
        # Get the latest values
        windspeed = data['kodeData0411'][-1] if data['kodeData0411'] else DEFAULT_VALUES['kodeData0411']
        windspeed_value = f"{windspeed}m/s"
        
        # Create windspeed graph with properly aligned x and y values
        windspeed_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0411']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0411']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0411'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                windspeed_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                windspeed_fig.update_layout(
                    title="Windspeed Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Windspeed (m/s)", range=[0, 70]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=300,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                windspeed_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                windspeed_fig.update_layout(
                    title="Windspeed Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Windspeed (m/s)", range=[0, 70]),
                    height=300,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating windspeed graph: {e}")
            # Create a basic empty chart if there's an error
            windspeed_fig = go.Figure()
            windspeed_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        return windspeed_value, windspeed_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", default_fig
    
# Separate callback for rainfall layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'rainfall-display'}, 'children', allow_duplicate=True),
     Output('rainfall-graph', 'figure')],
    [Input('interval_rainfall', 'n_intervals')],
    prevent_initial_call=True
)
def update_rainfall_dashboard(n):
    try:
        # Default values
        rainfall_value = "N/A"
        
        # Empty figures with proper layout
        empty_rainfall_fig = go.Figure(layout=dict(
            title="Rainfall Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="Rainfall (mm)", range=[0, 70]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0511'] or not data['waktu']:
            return rainfall_value, empty_rainfall_fig
        
        # Get the latest values
        rainfall = data['kodeData0511'][-1] if data['kodeData0511'] else DEFAULT_VALUES['kodeData0511']
        rainfall_value = f"{rainfall}mm"
        
        # Create rainfall graph with properly aligned x and y values
        rainfall_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0511']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0511']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0511'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                rainfall_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                rainfall_fig.update_layout(
                    title="Rainfall Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="Rainfall (mm)", range=[0, 70]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=300,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                rainfall_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                rainfall_fig.update_layout(
                    title="Rainfall Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="Rainfall (mm)", range=[0, 70]),
                    height=300,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating rainfall graph: {e}")
            # Create a basic empty chart if there's an error
            rainfall_fig = go.Figure()
            rainfall_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        return rainfall_value, rainfall_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", default_fig
    
# Separate callback for co2 layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'co2-display'}, 'children', allow_duplicate=True),
     Output('co2-graph', 'figure')],
    [Input('interval_co2', 'n_intervals')],
    prevent_initial_call=True
)
def update_co2_dashboard(n):
    try:
        # Default values
        co2_value = "N/A"
        
        # Empty figures with proper layout
        co2_fig = go.Figure(layout=dict(
            title="CO2 Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="CO2 (PPM)", range=[0, 2000]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0311'] or not data['waktu']:
            return co2_value, co2_fig
        
        # Get the latest values
        co2 = data['kodeData0311'][-1] if data['kodeData0311'] else DEFAULT_VALUES['kodeData0311']
        co2_value = f"{co2}PPM"
        

        # Create co2 graph with properly aligned x and y values
        co2_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0311']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0311']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0311'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                co2_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                co2_fig.update_layout(
                    title="CO2 Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="CO2 (PPM)", range=[0, 2000]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=300,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                co2_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                co2_fig.update_layout(
                    title="CO2 Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="CO2 (PPM)", range=[0, 2000]),
                    height=300,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating co2 graph: {e}")
            # Create a basic empty chart if there's an error
            co2_fig = go.Figure()
            co2_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        return co2_value, co2_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", default_fig
    
# Separate callback for PAR layout - Completely revised version
@app_dash.callback(
    [Output({'type': 'sensor-value', 'id': 'par-display'}, 'children', allow_duplicate=True),
     Output('par-graph', 'figure')],
    [Input('interval_par', 'n_intervals')],
    prevent_initial_call=True
)
def update_par_dashboard(n):
    try:
        # Default values
        par_value = "N/A"
        
        # Empty figures with proper layout
        par_fig = go.Figure(layout=dict(
            title="PAR Trend",
            xaxis=dict(title="Time"),
            yaxis=dict(title="PAR (μmol/m²/s)", range=[0, 2500]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeData0611'] or not data['waktu']:
            return par_value, par_fig
        
        # Get the latest values
        par = data['kodeData0611'][-1] if data['kodeData0611'] else DEFAULT_VALUES['kodeData0611']
        par_value = f"{par}μmol/m²/s"
        
        # Create par graph with properly aligned x and y values
        par_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeData0611']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeData0611']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeData0611'][i] for i in indices]
                
                # Create x values (0, 1, 2) for plotting
                x_plot = list(range(num_points))
                
                # Add the simplified line
                par_fig.add_trace(go.Scatter(
                    x=x_plot,  # Just use 0, 1, 2 for x values
                    y=selected_values,
                    mode='lines',
                    line=dict(color='#4B86FF', width=3, shape='spline', smoothing=1.3),
                    fill='tozeroy',
                    fillcolor='rgba(75, 134, 255, 0.2)',
                    showlegend=False
                ))
                
                # Set up the axis with only 3 ticks
                par_fig.update_layout(
                    title="PAR Trend",
                    xaxis=dict(
                        title="Time",
                        tickmode='array',
                        tickvals=x_plot,  # [0, 1, 2]
                        ticktext=selected_timestamps,
                        tickangle=0
                    ),
                    yaxis=dict(title="PAR (μmol/m²/s)", range=[0, 2500]),
                    margin=dict(l=40, r=20, t=40, b=30),
                    height=300,
                    plot_bgcolor='rgba(250, 250, 250, 0.9)',
                    showlegend=False
                )
                
            else:
                # Fallback for insufficient data
                par_fig.add_trace(go.Scatter(
                    x=[0, 1],
                    y=[0, 0],
                    mode='lines',
                    line=dict(color='#4B86FF', width=3),
                    showlegend=False
                ))
                par_fig.update_layout(
                    title="PAR Trend - Insufficient Data",
                    xaxis=dict(title="Time"),
                    yaxis=dict(title="PAR (μmol/m²/s)", range=[0, 2500]),
                    height=300,
                    showlegend=False
                )
                
        except Exception as e:
            print(f"Error creating par graph: {e}")
            # Create a basic empty chart if there's an error
            par_fig = go.Figure()
            par_fig.add_annotation(
                text=f"Error creating chart: {str(e)}",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False
            )
        return par_value, par_fig
    
    except Exception as e:
        print(f"Error in update_th_in_dashboard: {e}")
        # Return default values if there's an error
        default_fig = go.Figure(layout=dict(
            title="Data Unavailable",
            annotations=[dict(
                text="Error loading data",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )]
        ))
        return "N/A", default_fig

# Callbacks to update the realtime table
@app_dash.callback(
    Output('realtime-table', 'data'),
    Input('interval_mcs', 'n_intervals')
)
def update_realtime_table(n_intervals):
    # Prepare data for the table
    table_data = []
    
    # Only add rows if we have data
    if len(data['waktu']) > 0:
        # Get the most recent 10 data points (or fewer if less than 10 available)
        num_records = min(10, len(data['waktu']))
        start_index = max(0, len(data['waktu']) - num_records)
        
        # Loop through the most recent data points in reverse order (newest first)
        for i in range(len(data['waktu']) - 1, start_index - 1, -1):
            try:
                table_row = {
                    "Time": data['waktu'][i] if i < len(data['waktu']) else "N/A",
                    "Temp In (°C)": safe_float_convert(
                        data['kodeData0211'][i] if i < len(data['kodeData0211']) else None
                    ),
                    "Humidity In (%)": safe_float_convert(
                        data['kodeData0212'][i] if i < len(data['kodeData0212']) else None
                    ),
                    "Temp Out (°C)": safe_float_convert(
                        data['kodeData0711'][i] if i < len(data['kodeData0711']) else None
                    ),
                    "Humidity Out (%)": safe_float_convert(
                        data['kodeData0712'][i] if i < len(data['kodeData0712']) else None
                    ),
                    "PAR (μmol/m²/s)": safe_float_convert(
                        data['kodeData0611'][i] if i < len(data['kodeData0611']) else None
                    ),
                    "CO2 (PPM)": safe_float_convert(
                        data['kodeData0311'][i] if i < len(data['kodeData0311']) else None
                    ),
                    "Windspeed (m/s)": safe_float_convert(
                        data['kodeData0411'][i] if i < len(data['kodeData0411']) else None
                    ),
                    "Rainfall (mm)": safe_float_convert(
                        data['kodeData0511'][i] if i < len(data['kodeData0511']) else None
                    ),
                    "Voltage AC (V)": safe_float_convert(
                        data['kodeData0911'][i] if i < len(data['kodeData0911']) else None
                    ),
                    "Current AC (A)": safe_float_convert(
                        data['kodeData0912'][i] if i < len(data['kodeData0912']) else None
                    ),
                    "Power AC (W)": safe_float_convert(
                        data['kodeData0913'][i] if i < len(data['kodeData0913']) else None
                    ),
                }
                table_data.append(table_row)
            except (IndexError, ValueError) as e:
                # Handle potential errors when accessing data
                print(f"Error updating table row {i}: {e}")
    
    # If no data was added or there was an error, add a row of N/A values
    if not table_data:
        table_data.append({
            "Time": "N/A",
            "Temp In (°C)": "N/A",
            "Humidity In (%)": "N/A",
            "Temp Out (°C)": "N/A", 
            "Humidity Out (%)": "N/A",
            "PAR (μmol/m²/s)": "N/A", 
            "CO2 (PPM)": "N/A",
            "Windspeed (m/s)": "N/A", 
            "Rainfall (mm)": "N/A"
        })
    
    return table_data
    
# Callbacks to logout
@app_dash.callback(
    Output("logout-redirect", "href"),
    Input("logout-button", "n_clicks")
)
def logout_redirect(n_clicks):
    if n_clicks:
        return "/logout"  # Redirects to Flask route
    return None

# Callbacks to login
@app_dash.callback(
    Output("login-redirect", "href"),
    Input("login-button", "n_clicks")
)
def login_redirect(n_clicks):
    if n_clicks:
        return "/login"  # Redirects to Flask route
    return None

# Callback for GPS map
@app_dash.callback(
    [Output('gps-map', 'figure'),
     Output('current-location-text', 'children'),
     Output('current-coordinates', 'children')],
    [Input('interval_gps', 'n_intervals')]
)
def update_gps_data(n_intervals):
    """Update GPS map and location information using MQTT data"""
    # Add eFarming Corpora Community to LOCATIONS
    efarming_location = {"name": "eFarming Corpora Community", "lat": -6.880044, "lon": 107.6772643}
    
    # Create a local copy of locations including eFarming
    locations = LOCATIONS + [efarming_location]
    
    # Safe GPS coordinate conversion
    def safe_coordinate_convert(coord_value, fallback_value):
        """Safely convert coordinate value to float"""
        try:
            if coord_value is None:
                return fallback_value
            if isinstance(coord_value, str):
                if coord_value == "-" or coord_value.strip() == "":
                    return fallback_value
                return float(coord_value)
            if isinstance(coord_value, (int, float)):
                return float(coord_value)
            return fallback_value
        except (ValueError, TypeError):
            return fallback_value
    
    # Check if we have GPS data from MQTT
    if data["kodeData1011"] and data["kodeData1012"]:
        # Use the latest GPS coordinates from the MQTT data with safe conversion
        raw_lat = data["kodeData1011"][-1] if len(data["kodeData1011"]) > 0 else None
        raw_lon = data["kodeData1012"][-1] if len(data["kodeData1012"]) > 0 else None
        
        current_lat = safe_coordinate_convert(raw_lat, efarming_location["lat"])
        current_lon = safe_coordinate_convert(raw_lon, efarming_location["lon"])
        
        # Only search for closest location if we have valid coordinates (not fallback)
        if (raw_lat is not None and raw_lat != "-" and 
            raw_lon is not None and raw_lon != "-"):
            # Find closest known location
            min_distance = float('inf')
            location_name = "Unknown Location"
            for loc in locations:
                dist = ((loc["lat"] - current_lat)**2 + (loc["lon"] - current_lon)**2)**0.5
                if dist < min_distance:
                    min_distance = dist
                    location_name = f"Near {loc['name']}"
        else:
            location_name = "eFarming Corpora Community (Default)"
    else:
        # Fallback if no MQTT data is available
        current_lat = efarming_location["lat"]
        current_lon = efarming_location["lon"]
        location_name = "eFarming Corpora Community (Default)"
    
    # Create the map figure
    fig = go.Figure()
    
    # Add main device marker
    fig.add_trace(go.Scattermapbox(
        lat=[current_lat],
        lon=[current_lon],
        mode='markers',
        marker=dict(
            size=15,
            color='red',
        ),
        text=["Current Device Location"],
        name="Device"
    ))
    
    # Add known locations as reference points
    fig.add_trace(go.Scattermapbox(
        lat=[loc["lat"] for loc in locations],
        lon=[loc["lon"] for loc in locations],
        mode='markers',
        marker=dict(
            size=10,
            color='blue',
        ),
        text=[loc["name"] for loc in locations],
        name="Reference Points"
    ))
    
    # Configure the map layout
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=current_lat, lon=current_lon),
            zoom=15,
            uirevision=f"{current_lat}_{current_lon}"
        ),
        margin=dict(l=0, r=0, t=0, b=0),
        height=500,
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="left",
            x=0.01,
            bgcolor="rgba(255,255,255,0.8)"
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
    )
    
    # Format coordinates as a string with 6 decimal places
    coordinates_text = f"{current_lat:.6f}, {current_lon:.6f}"
    
    return fig, location_name, coordinates_text

# Updated Alarm Callback with Circle Status
@app_dash.callback(
    [Output("temp-in-alarm", "children"),
     Output("temp-in-berita", "children"),
     Output("temp-in-circle", "className"),
     Output("humidity-in-alarm", "children"),
     Output("humidity-in-berita", "children"),
     Output("humidity-in-circle", "className"),
     Output("temp-out-alarm", "children"),
     Output("temp-out-berita", "children"),
     Output("temp-out-circle", "className"),
     Output("humidity-out-alarm", "children"),
     Output("humidity-out-berita", "children"),
     Output("humidity-out-circle", "className"),
     Output("par-alarm", "children"),
     Output("par-berita", "children"),
     Output("par-circle", "className"),
     Output("co2-alarm", "children"),
     Output("co2-berita", "children"),
     Output("co2-circle", "className"),
     Output("windspeed-alarm", "children"),
     Output("windspeed-berita", "children"),
     Output("windspeed-circle", "className"),
     Output("rainfall-alarm", "children"),
     Output("rainfall-berita", "children"),
     Output("rainfall-circle", "className"),
     Output("voltage-ac-alarm", "children"),
     Output("voltage-ac-berita", "children"),
     Output("voltage-ac-circle", "className"),
     Output("current-ac-alarm", "children"),
     Output("current-ac-berita", "children"),
     Output("current-ac-circle", "className"),
     Output("power-ac-alarm", "children"),
     Output("power-ac-berita", "children"),
     Output("power-ac-circle", "className")],
    [Input("interval-alarm", "n_intervals")]
)
def update_alarm_values(n):
    def get_circle_class(kode_alarm):
        if kode_alarm in [1, 4]:
            return "status-circle status-red"
        elif kode_alarm in [2, 3]:
            return "status-circle status-yellow"
        elif kode_alarm == 0:
            return "status-circle status-green"
        else:  # kode_alarm == 0
            return "status-circle status-black"
    
    return (
        alarm_data['kodeAlarm0211'],
        alarm_data['berita0211'],
        get_circle_class(alarm_data['kodeAlarm0211']),
        alarm_data['kodeAlarm0212'],
        alarm_data['berita0212'],
        get_circle_class(alarm_data['kodeAlarm0212']),
        alarm_data['kodeAlarm0711'],
        alarm_data['berita0711'],
        get_circle_class(alarm_data['kodeAlarm0711']),
        alarm_data['kodeAlarm0712'],
        alarm_data['berita0712'],
        get_circle_class(alarm_data['kodeAlarm0712']),
        alarm_data['kodeAlarm0611'],
        alarm_data['berita0611'],
        get_circle_class(alarm_data['kodeAlarm0611']),
        alarm_data['kodeAlarm0311'],
        alarm_data['berita0311'],
        get_circle_class(alarm_data['kodeAlarm0311']),
        alarm_data['kodeAlarm0411'],
        alarm_data['berita0411'],
        get_circle_class(alarm_data['kodeAlarm0411']),
        alarm_data['kodeAlarm0511'],
        alarm_data['berita0511'],
        get_circle_class(alarm_data['kodeAlarm0511']),
        alarm_data['kodeAlarm0911'],
        alarm_data['berita0911'],
        get_circle_class(alarm_data['kodeAlarm0911']),
        alarm_data['kodeAlarm0912'],
        alarm_data['berita0912'],
        get_circle_class(alarm_data['kodeAlarm0912']),
        alarm_data['kodeAlarm0913'],
        alarm_data['berita0913'],
        get_circle_class(alarm_data['kodeAlarm0913'])
    )

# Callback for prediction graphs temperature and humidity indoor
@app_dash.callback(
    [Output('temp-prediction-graph', 'figure'),
     Output('humidity-prediction-graph', 'figure')],
    [Input('interval_thin', 'n_intervals')]
)
def update_th_in_prediction_graphs(n):
# Temperature prediction graph
    temp_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        temp_predictions = []
        
        # Create timestamps and get prediction values for next 1-5 minutes
        # Using kodeData0213 to kodeData0217 for temperature predictions
        temp_codes = ['kodeData0213', 'kodeData0214', 'kodeData0215', 'kodeData0216', 'kodeData0217']
        
        for i, pred_key in enumerate(temp_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                temp_predictions.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                temp_predictions.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"Temp predictions: {temp_predictions}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, temp_predictions) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            temp_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Temperature Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            temp_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            temp_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Temperature Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    temp_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="°C",
        height=97,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Humidity prediction graph
    humidity_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        humidity_predictions = []

        # Create timestamps and get prediction values for next 1-5 minutes
        humidity_codes = ['kodeData0218', 'kodeData0219', 'kodeData0220', 'kodeData0221', 'kodeData0222']
        
        for i, pred_key in enumerate(humidity_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                humidity_predictions.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                humidity_predictions.append(None)
        
        # Debug: Print the values to check
        print(f"Humidity future times: {future_times}")
        print(f"Humidity predictions: {humidity_predictions}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, humidity_predictions) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            humidity_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Humidity Prediction',
                line=dict(color='blue', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            humidity_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            humidity_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Humidity Prediction',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    humidity_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="%",
        height=97,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return temp_fig, humidity_fig

# Callback for prediction graphs temperature and humidity outdoor
@app_dash.callback(
    [Output('temp-prediction-out-graph', 'figure'),
     Output('humidity-prediction-out-graph', 'figure')],
    [Input('interval_thout', 'n_intervals')]
)
def update_th_out_prediction_graphs(n):
    # Temperature prediction graph
    temp_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        temp_predictions = []

        # Create timestamps and get prediction values for next 1-5 minutes
        temp_codes = ['kodeData0713', 'kodeData0714', 'kodeData0715', 'kodeData0716', 'kodeData0717']
        # Using kodeData0713 to kodeData0717 for temperature predictions
        for i, pred_key in enumerate(temp_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                temp_predictions.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                temp_predictions.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"Temp predictions: {temp_predictions}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, temp_predictions) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            temp_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Temperature Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            temp_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            temp_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Temperature Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    temp_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="°C",
        height=97,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    # Humidity prediction graph
    humidity_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        humidity_predictions = []

        # Create timestamps and get prediction values for next 1-5 minutes
        humidity_codes = ['kodeData0718', 'kodeData0719', 'kodeData0720', 'kodeData0721', 'kodeData0722']
        
        for i, pred_key in enumerate(humidity_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                humidity_predictions.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                humidity_predictions.append(None)
        
        # Debug: Print the values to check
        print(f"Humidity future times: {future_times}")
        print(f"Humidity predictions: {humidity_predictions}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, humidity_predictions) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            humidity_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Humidity Prediction',
                line=dict(color='blue', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            humidity_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            humidity_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Humidity Prediction',
                line=dict(color='blue', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    humidity_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="%",
        height=97,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return temp_fig, humidity_fig

# Callback for prediction graphs co2
@app_dash.callback(
    Output('co2-prediction-graph', 'figure'),
    [Input('interval_co2', 'n_intervals')]
)
def update_co2_prediction_graphs(n):
    # Temperature prediction graph
    co2_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        co2_prediction = []

        # Create timestamps and get prediction values for next 1-5 minutes
        co2_codes = ['kodeData0312', 'kodeData0313', 'kodeData0314', 'kodeData0315', 'kodeData0316']
        
        for i, pred_key in enumerate(co2_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                co2_prediction.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                co2_prediction.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"CO2 predictions: {co2_prediction}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, co2_prediction) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            co2_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='CO2 Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            co2_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            co2_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='CO2 Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    co2_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="PPM",
        height=258,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return co2_fig

# Callback for prediction graphs par
@app_dash.callback(
    Output('par-prediction-graph', 'figure'),
    [Input('interval_par', 'n_intervals')]
)
def update_par_prediction_graphs(n):
    # Temperature prediction graph
    par_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        par_prediction = []
        
        # Create timestamps and get prediction values for next 1-5 minutes
        par_codes = ['kodeData0612', 'kodeData0613', 'kodeData0614', 'kodeData0615', 'kodeData0616']
        
        for i, pred_key in enumerate(par_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                par_prediction.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                par_prediction.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"PAR predictions: {par_prediction}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, par_prediction) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            par_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='PAR Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            par_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            par_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='PAR Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    par_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="μmol/m²/s",
        height=258,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return par_fig

# Callback for prediction graphs windspeed
@app_dash.callback(
    Output('windspeed-prediction-graph', 'figure'),
    [Input('interval_windspeed', 'n_intervals')]
)
def update_windspeed_prediction_graphs(n):
    # Temperature prediction graph
    windspeed_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        windspeed_prediction = []
        
        # Create timestamps and get prediction values for next 1-5 minutes
        windspeed_codes = ['kodeData0412', 'kodeData0413', 'kodeData0414', 'kodeData0415', 'kodeData0416']
        
        for i, pred_key in enumerate(windspeed_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                windspeed_prediction.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                windspeed_prediction.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"Windspeed predictions: {windspeed_prediction}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, windspeed_prediction) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            windspeed_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Windspeed Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            windspeed_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            windspeed_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Windspeed Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    windspeed_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="m/s",
        height=258,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return windspeed_fig

# Callback for prediction graphs rainfall
@app_dash.callback(
    Output('rainfall-prediction-graph', 'figure'),
    [Input('interval_rainfall', 'n_intervals')]
)
def update_rainfall_prediction_graphs(n):
    # Temperature prediction graph
    rainfall_fig = go.Figure()
    
    if data['waktu'] and len(data['waktu']) > 0:
        # Get the last timestamp and ensure it's a proper datetime
        last_time = data['waktu'][-1]
        
        # Convert to pandas datetime if it's not already
        if not isinstance(last_time, pd.Timestamp):
            last_time = pd.to_datetime(last_time)
        
        future_times = []
        rainfall_prediction = []
        
        # Create timestamps and get prediction values for next 1-5 minutes
        rainfall_codes = ['kodeData0512', 'kodeData0513', 'kodeData0514', 'kodeData0515', 'kodeData0516']
        
        for i, pred_key in enumerate(rainfall_codes, 1):
            # Use datetime arithmetic instead of pd.Timedelta
            future_time = last_time + pd.Timedelta(minutes=i)
            future_times.append(future_time)
            
            # Get the latest prediction value for each minute ahead
            if pred_key in prediction_data and prediction_data[pred_key] and len(prediction_data[pred_key]) > 0:
                rainfall_prediction.append(prediction_data[pred_key][-1])
            else:
                # Use a reasonable default or interpolation
                rainfall_prediction.append(None)
        
        # Debug: Print the values to check
        print(f"Future times: {future_times}")
        print(f"Rainfall predictions: {rainfall_prediction}")
        
        # Only plot if we have prediction data
        valid_predictions = [(t, p) for t, p in zip(future_times, rainfall_prediction) if p is not None]
        
        if valid_predictions and len(valid_predictions) > 2:
            times, preds = zip(*valid_predictions)
            
            # Apply smoothing using np.linspace approach similar to PAR callback
            num_points = len(valid_predictions)
            
            # Create evenly spaced indices
            indices = np.linspace(0, num_points-1, num_points, dtype=int)
            
            # Get the selected timestamps and prediction values
            selected_timestamps = [times[i] for i in indices]
            selected_values = [preds[i] for i in indices]
            
            # Create x values for plotting
            x_plot = list(range(num_points))
            
            rainfall_fig.add_trace(go.Scatter(
                x=x_plot,
                y=selected_values,
                mode='lines+markers',
                name='Rainfall Prediction',
                line=dict(color='red', width=2, shape='spline', smoothing=1.3),
                marker=dict(size=6),
                connectgaps=False,
                showlegend=False
            ))
            
            # Update layout with custom x-axis labels
            rainfall_fig.update_layout(
                xaxis=dict(
                    title="Time",
                    tickmode='array',
                    tickvals=x_plot,
                    ticktext=[t.strftime('%H:%M') for t in selected_timestamps],
                    tickangle=0,
                    showgrid=True,
                    gridcolor='lightgray'
                )
            )
        elif valid_predictions:
            # Fallback for insufficient data points
            times, preds = zip(*valid_predictions)
            rainfall_fig.add_trace(go.Scatter(
                x=list(times),
                y=list(preds),
                mode='lines+markers',
                name='Rainfall Prediction',
                line=dict(color='red', width=2),
                marker=dict(size=6),
                connectgaps=False
            ))
    
    rainfall_fig.update_layout(
        title="",
        xaxis_title="Time",
        yaxis_title="mm",
        height=258,
        margin=dict(l=40, r=20, t=20, b=40),
        showlegend=False,
        yaxis=dict(
            showgrid=True,
            gridcolor='lightgray'
        ),
        plot_bgcolor='white',
        paper_bgcolor='white'
    )
    
    return rainfall_fig

# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN th_in.py
@app_dash.callback(
    Output('historical-table-th-in', 'data'),
    Input('interval_thin', 'n_intervals')
)
def update_th_in_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'temperature_in_historical': row.get('Temp In'),
                'humidity_in_historical': row.get('Humid In')
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error

# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN th_out.py
@app_dash.callback(
    Output('historical-table-th-out', 'data'),
    Input('interval_thout', 'n_intervals')
)
def update_th_out_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'temperature_out_historical': row.get('Temp Out'),
                'humidity_out_historical': row.get('Humid Out')
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error
    
# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN par.py
@app_dash.callback(
    Output('historical-table-par', 'data'),
    Input('interval_par', 'n_intervals')
)
def update_par_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'par-historical': row.get('PAR'),
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error
    
# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN rainfall.py
@app_dash.callback(
    Output('historical-table-rainfall', 'data'),
    Input('interval_rainfall', 'n_intervals')
)
def update_rainfall_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'rainfall-historical': row.get('Rainfall'),
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error

# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN windspeed.py
@app_dash.callback(
    Output('historical-table-windspeed', 'data'),
    Input('interval_windspeed', 'n_intervals')
)
def update_windspeed_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'windspeed-historical': row.get('Windspeed'),
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error

# CALLBACK TO UPDATE THE HISTORICAL DATA TABLE IN co2.py
@app_dash.callback(
    Output('historical-table-co2', 'data'),
    Input('interval_co2', 'n_intervals')
)
def update_co2_historical_table(n):
    try:
        # 1. Authenticate with Google Sheets (ensure 'credentials.json' is in your root directory)
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
        client = gspread.authorize(creds)

        # 2. Open the spreadsheet and select the first sheet
        sheet = client.open("microclimate_database").sheet1

        # 3. Get all data, excluding the header row
        records = sheet.get_all_records()
        
        # 4. If there's no data, return an empty list
        if not records:
            return []

        # 5. Get the last 20 records for display and reverse them to show the latest on top
        latest_records = records[-20:]
        latest_records.reverse()

        # 6. Format the data to match the DataTable column IDs
        #    Spreadsheet columns: 'Time', 'Temp In', 'Humid In'
        #    DataTable columns: 'time', 'temperature_in_historical', 'humidity_in_historical'
        table_data = []
        for row in latest_records:
            # Extract only the time part (e.g., '21:00') from the full datetime string
            time_value = str(row.get('Time', ''))

            table_data.append({
                'time': time_value,
                'co2-historical': row.get('CO2'),
            })
            
        return table_data

    except gspread.exceptions.SpreadsheetNotFound:
        print("Error: Spreadsheet 'microclimate_database' not found. Check the name and sharing permissions.")
        return [] # Return empty data to prevent the app from crashing
    except Exception as e:
        print(f"An error occurred while updating the historical table: {e}")
        return [] # Return empty data on any other error
    
# Run server
if __name__ == '__main__':
    server.run(server.run(host='0.0.0.0', port=5000))
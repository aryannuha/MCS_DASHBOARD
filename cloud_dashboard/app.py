# Author: Ammar Aryan Nuha
# Deklarasi library yang digunakan
from flask import Flask, render_template, redirect, url_for, request, flash, session
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
from datetime import datetime
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
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

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

@server.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')  # Redirect to public home page
# end of flask route

# Integrate Dash app
app_dash = dash.Dash(__name__, server=server, url_base_pathname='/dash/', external_stylesheets=[dbc.themes.BOOTSTRAP], title='MCS Dashboard', suppress_callback_exceptions=True, assets_folder='assets')
 
@app_dash.server.before_request
def restrict_dash_pages():
    if request.path.startswith('/dash/engineer') and not session.get('_user_id'):
        return redirect(url_for('login'))

# data storage
data = {
    'waktu': [],      # Time values
    'kodeDataSuhuIn': [],       # Temperature values 
    'kodeDataKelembabanIn': [], # Humidity values
    'kodeDataSuhuOut': [],   # Outdoor temperature values
    'kodeDataKelembabanOut': [], # Outdoor humidity values
    'kodeDataCo2': [],        # CO2 values
    'kodeDataWindspeed': [],  # Wind speed values
    'kodeDataRainfall': [],    # Rainfall values
    'kodeDataPar': [],    # PAR values
    'kodeDataLat': [],   # Latitude values
    'kodeDataLon': []    # Longitude values
}

# Alarm data storage
alarm_data = {
    'kodeAlarmSuhuIn': 0,
    'beritaSuhuIn': 'Normal',
    'kodeAlarmKelembabanIn': 0,
    'beritaKelembabanIn': 'Normal',
    'kodeAlarmSuhuOut': 0,
    'beritaSuhuOut': 'Normal',
    'kodeAlarmKelembabanOut': 0,
    'beritaKelembabanOut': 'Normal',
    'kodeAlarmCo2': 0,
    'beritaCo2': 'Normal',
    'kodeAlarmWindspeed': 0,
    'beritaWindspeed': 'Normal',
    'kodeAlarmRainfall': 0,
    'beritaRainfall': 'Normal',
    'kodeAlarmPar': 0,
    'beritaPar': 'Normal',
}

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

# TOPIC FOR DATA
TOPIC_SUHU = "mcs/kodeDataSuhuIn"
TOPIC_KELEMBABAN = "mcs/kodeDataKelembabanIn"
TOPIC_SUHU_OUT = "mcs/kodeDataSuhuOut"
TOPIC_KELEMBABAN_OUT = "mcs/kodeDataKelembabanOut"
TOPIC_CO2 = "mcs/kodeDataCo2"
TOPIC_WINDSPEED = "mcs/kodeDataWindspeed"
TOPIC_RAINFALL = "mcs/kodeDataRainfall"
TOPIC_PAR = "mcs/kodeDataPar"
TOPIC_LAT = "mcs/kodeDataLat"
TOPIC_LON = "mcs/kodeDataLon"

# TOPIC FOR ALARM
TOPIC_ALARM_SUHU_IN = "mcs/kodeAlarmSuhuIn"
TOPIC_ALARM_KELEMBABAN_IN = "mcs/kodeAlarmKelembabanIn"
TOPIC_ALARM_SUHU_OUT = "mcs/kodeAlarmSuhuOut"
TOPIC_ALARM_KELEMBABAN_OUT = "mcs/kodeAlarmKelembabanOut"
TOPIC_ALARM_CO2 = "mcs/kodeAlarmCo2"
TOPIC_ALARM_WINDSPEED = "mcs/kodeAlarmWindspeed"
TOPIC_ALARM_RAINFALL = "mcs/kodeAlarmRainfall"
TOPIC_ALARM_PAR = "mcs/kodeAlarmPar"

# TOPIC FOR BERITA
TOPIC_BERITA_SUHU_IN = "mcs/beritaSuhuIn"
TOPIC_BERITA_KELEMBABAN_IN = "mcs/beritaKelembabanIn"
TOPIC_BERITA_SUHU_OUT = "mcs/beritaSuhuOut"
TOPIC_BERITA_KELEMBABAN_OUT = "mcs/beritaKelembabanOut"
TOPIC_BERITA_CO2 = "mcs/beritaCo2"
TOPIC_BERITA_WINDSPEED = "mcs/beritaWindspeed"
TOPIC_BERITA_RAINFALL = "mcs/beritaRainfall"
TOPIC_BERITA_PAR = "mcs/beritaPar"

# MQTT Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ Broker")
        client.subscribe([(TOPIC_SUHU, 0), (TOPIC_KELEMBABAN, 0),
                          (TOPIC_SUHU_OUT, 0), (TOPIC_KELEMBABAN_OUT, 0),
                          (TOPIC_CO2, 0), (TOPIC_WINDSPEED, 0), 
                          (TOPIC_RAINFALL, 0), (TOPIC_PAR, 0),
                          (TOPIC_LAT, 0),  (TOPIC_LON, 0),
                          (TOPIC_ALARM_SUHU_IN, 0), (TOPIC_ALARM_KELEMBABAN_IN, 0),
                          (TOPIC_ALARM_SUHU_OUT, 0), (TOPIC_ALARM_KELEMBABAN_OUT, 0),
                          (TOPIC_ALARM_CO2, 0), (TOPIC_ALARM_WINDSPEED, 0),
                          (TOPIC_ALARM_RAINFALL, 0), (TOPIC_ALARM_PAR, 0),
                          (TOPIC_BERITA_SUHU_IN, 0), (TOPIC_BERITA_KELEMBABAN_IN, 0),
                          (TOPIC_BERITA_SUHU_OUT, 0), (TOPIC_BERITA_KELEMBABAN_OUT, 0),
                          (TOPIC_BERITA_CO2, 0), (TOPIC_BERITA_WINDSPEED, 0),
                          (TOPIC_BERITA_RAINFALL, 0), (TOPIC_BERITA_PAR, 0)
                          ])  # Subscribe ke topik suhu & kelembaban
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global data, alarm_data
    try:
        topic = msg.topic.split('/')[-1]  # Get the last part of the topic (e.g., 'suhu' from 'esp32/suhu')
        
        # Process regular data topics
        if topic in ['kodeDataSuhuIn', 'kodeDataKelembabanIn', 'kodeDataSuhuOut', 'kodeDataKelembabanOut',
                    'kodeDataCo2', 'kodeDataWindspeed', 'kodeDataRainfall', 'kodeDataPar',
                    'kodeDataLat', 'kodeDataLon']:
            payload = float(msg.payload.decode())
            current_time = datetime.now(tz=pytz.timezone('Asia/Jakarta')).strftime('%H:%M:%S')
            
            if len(data[topic]) >= 20:  # Keep only last 20 points
                data[topic] = data[topic][1:]
            data[topic].append(payload)
            
            # Keep waktu list in sync with the latest data addition
            # This ensures all lists have the same length
            if topic == 'kodeDataSuhuIn':  # Only update waktu when temperature data comes in
                if len(data['waktu']) >= 20:
                    data['waktu'] = data['waktu'][1:]
                data['waktu'].append(current_time)
        
        # Process alarm code topics
        elif topic.startswith('kodeAlarm'):
            # For example: 'kodeAlarmSuhuIn'
            try:
                # Parse as integer for alarm codes
                alarm_value = int(msg.payload.decode())
                alarm_data[topic] = alarm_value
            except ValueError:
                print(f"Error parsing alarm value for {topic}: {msg.payload.decode()}")
        
        # Process berita (alert message) topics
        elif topic.startswith('berita'):
            # For example: 'beritaSuhuIn'
            # Keep as string for berita messages
            berita_value = msg.payload.decode()
            alarm_data[topic] = berita_value

    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# UPDATED: MQTT Client with error handling
def setup_mqtt_client():
    """Setup MQTT client with proper error handling"""
    try:
        client = mqtt.Client()
        client.username_pw_set(USERNAME, PASSWORD)
        client.tls_set_context(ssl_context)
        client.on_connect = on_connect
        client.on_message = on_message
        
        # Add connection error handling
        def on_disconnect(client, userdata, rc):
            if rc != 0:
                print(f"Unexpected MQTT disconnection. Return code: {rc}")
        
        client.on_disconnect = on_disconnect
        
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

# Initialize MQTT client
mqtt_client = setup_mqtt_client()
if mqtt_client:
    # Run MQTT in thread only if connection successful
    threading.Thread(target=mqtt_client.loop_forever, daemon=True).start()
else:
    print("MQTT client not started due to connection issues")

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
        suhu = data['kodeDataSuhuIn'][-1] if data['kodeDataSuhuIn'] else 0
        kelembaban = data['kodeDataKelembabanIn'][-1] if data['kodeDataKelembabanIn'] else 0
        suhu_out = data['kodeDataSuhuOut'][-1] if data['kodeDataSuhuOut'] else 0
        kelembaban_out = data['kodeDataKelembabanOut'][-1] if data['kodeDataKelembabanOut'] else 0
        co2 = data['kodeDataCo2'][-1] if data['kodeDataCo2'] else 0
        windspeed = data['kodeDataWindspeed'][-1] if data['kodeDataWindspeed'] else 0
        rainfall = data['kodeDataRainfall'][-1] if data['kodeDataRainfall'] else 0
        par = data['kodeDataPar'][-1] if data['kodeDataPar'] else 0

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
            yaxis=dict(title="Humidity (%)", range=[40, 100]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeDataSuhuIn'] or not data['kodeDataKelembabanIn'] or not data['waktu']:
            return suhu_value, kelembaban_value, empty_temp_fig, empty_humid_fig
        
        # Get the latest values
        suhu = data['kodeDataSuhuIn'][-1] if data['kodeDataSuhuIn'] else 0
        kelembaban = data['kodeDataKelembabanIn'][-1] if data['kodeDataKelembabanIn'] else 0
        suhu_value = f"{suhu}°C"
        kelembaban_value = f"{kelembaban}%"
        
        # Create temperature graph with properly aligned x and y values
        temp_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataSuhuIn']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataSuhuIn']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataSuhuIn'][i] for i in indices]
                
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
            if len(data['waktu']) > 3 and len(data['kodeDataKelembabanIn']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataKelembabanIn']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataKelembabanIn'][i] for i in indices]
                
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
                    yaxis=dict(title="Humidity (%)", range=[40, 100]),
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
                    yaxis=dict(title="Humidity (%)", range=[40, 100]),
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
            yaxis=dict(title="Humidity (%)", range=[40, 100]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=150,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeDataSuhuOut'] or not data['kodeDataKelembabanOut'] or not data['waktu']:
            return suhu_value, kelembaban_value, empty_temp_fig, empty_humid_fig
        
        # Get the latest values
        suhu = data['kodeDataSuhuOut'][-1] if data['kodeDataSuhuOut'] else 0
        kelembaban = data['kodeDataKelembabanOut'][-1] if data['kodeDataKelembabanOut'] else 0
        suhu_value = f"{suhu}°C"
        kelembaban_value = f"{kelembaban}%"

        # Create temperature graph with properly aligned x and y values
        temp_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataSuhuOut']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataSuhuOut']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataSuhuOut'][i] for i in indices]
                
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
            if len(data['waktu']) > 3 and len(data['kodeDataKelembabanOut']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataKelembabanOut']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataKelembabanOut'][i] for i in indices]
                
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
                    yaxis=dict(title="Humidity (%)", range=[40, 100]),
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
                    yaxis=dict(title="Humidity (%)", range=[40, 100]),
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
        if not data['kodeDataWindspeed'] or not data['waktu']:
            return windspeed_value, empty_windspeed_fig
        
        # Get the latest values
        windspeed = data['kodeDataWindspeed'][-1] if data['kodeDataWindspeed'] else 0
        windspeed_value = f"{windspeed}m/s"
        
        # Create windspeed graph with properly aligned x and y values
        windspeed_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataWindspeed']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataWindspeed']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataWindspeed'][i] for i in indices]
                
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
            yaxis=dict(title="Rainfall (mm)", range=[0, 100]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeDataRainfall'] or not data['waktu']:
            return rainfall_value, empty_rainfall_fig
        
        # Get the latest values
        rainfall = data['kodeDataRainfall'][-1] if data['kodeDataRainfall'] else 0
        rainfall_value = f"{rainfall}mm"
        
        # Create rainfall graph with properly aligned x and y values
        rainfall_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataRainfall']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataRainfall']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataRainfall'][i] for i in indices]
                
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
                    yaxis=dict(title="Rainfall (mm)", range=[0, 100]),
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
                    yaxis=dict(title="Rainfall (mm)", range=[0, 100]),
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
            yaxis=dict(title="CO2 (PPM)", range=[300, 10000]),
            margin=dict(l=40, r=20, t=40, b=30),
            height=300,
            plot_bgcolor='rgba(240, 240, 240, 0.9)'
        ))
        
        # Check if we have data
        if not data['kodeDataCo2'] or not data['waktu']:
            return co2_value, co2_fig
        
        # Get the latest values
        co2 = data['kodeDataCo2'][-1] if data['kodeDataCo2'] else 0
        co2_value = f"{co2}PPM"
        

        # Create co2 graph with properly aligned x and y values
        co2_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataCo2']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataCo2']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataCo2'][i] for i in indices]
                
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
                    yaxis=dict(title="CO2 (PPM)", range=[300, 10000]),
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
                    yaxis=dict(title="CO2 (PPM)", range=[300, 10000]),
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
        if not data['kodeDataPar'] or not data['waktu']:
            return par_value, par_fig
        
        # Get the latest values
        par = data['kodeDataPar'][-1] if data['kodeDataPar'] else 0
        par_value = f"{par}μmol/m²/s"
        
        # Create par graph with properly aligned x and y values
        par_fig = go.Figure()

        try:
            # Ensure we have data to work with
            if len(data['waktu']) > 3 and len(data['kodeDataPar']) > 3:
                # We'll use only 3 data points for simplicity
                num_points = 4
                
                # Select evenly spaced indices from the data
                indices = np.linspace(0, min(len(data['waktu']), len(data['kodeDataPar']))-1, num_points, dtype=int)
                
                # Get the selected timestamps and temperature values
                selected_timestamps = [data['waktu'][i] for i in indices]
                selected_values = [data['kodeDataPar'][i] for i in indices]
                
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

# Add this function to help debug what's happening with your data
# and the table th_in
# @app_dash.callback(
#     Output('historical-table-th-in', 'data'),
#     [Input('interval_thin', 'n_intervals')]
# )
# def update_historical_table(n):
#     try:            
#         # Create table data from the last 4 entries
#         sample_size = min(2, len(data['waktu']))
#         table_data = []
        
#         for i in range(sample_size):
#             idx = -(i+1)  # Index from the end of the list
#             table_data.append({
#                 "time": data['waktu'][idx] if idx < len(data['waktu']) else "",
#                 "temperature_in_historical": f"{data['kodeDataSuhuIn'][idx]:.1f}%" if idx < len(data['kodeDataSuhuIn']) else "",
#                 "humidity_in_historical": f"{data['kodeDataKelembabanIn'][idx]:.1f}%" if idx < len(data['kodeDataKelembabanIn']) else ""
#             })
            
#         return table_data
#     except Exception as e:
#         print(f"Error in update_historical_table: {e}")
#         return [{}]

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
                    "Temp In (°C)": f"{float(data['kodeDataSuhuIn'][i]):.1f}" if i < len(data['kodeDataSuhuIn']) else "N/A",
                    "Humidity In (%)": f"{float(data['kodeDataKelembabanIn'][i]):.1f}" if i < len(data['kodeDataKelembabanIn']) else "N/A",
                    "Temp Out (°C)": f"{float(data['kodeDataSuhuOut'][i]):.1f}" if i < len(data['kodeDataSuhuOut']) else "N/A",
                    "Humidity Out (%)": f"{float(data['kodeDataKelembabanOut'][i]):.1f}" if i < len(data['kodeDataKelembabanOut']) else "N/A",
                    "PAR (μmol/m²/s)": f"{float(data['kodeDataPar'][i]):.1f}" if i < len(data['kodeDataPar']) else "N/A",
                    "CO2 (PPM)": f"{float(data['kodeDataCo2'][i]):.1f}" if i < len(data['kodeDataCo2']) else "N/A",
                    "Windspeed (m/s)": f"{float(data['kodeDataWindspeed'][i]):.1f}" if i < len(data['kodeDataWindspeed']) else "N/A",
                    "Rainfall (mm)": f"{float(data['kodeDataRainfall'][i]):.1f}" if i < len(data['kodeDataRainfall']) else "N/A"
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
    
    # Check if we have GPS data from MQTT
    if data["kodeDataLat"] and data["kodeDataLon"]:
        # Use the latest GPS coordinates from the MQTT data
        current_lat = data["kodeDataLat"][-1]
        current_lon = data["kodeDataLon"][-1]
        
        # Find closest known location
        min_distance = float('inf')
        location_name = "Unknown Location"
        for loc in locations:
            dist = ((loc["lat"] - current_lat)**2 + (loc["lon"] - current_lon)**2)**0.5
            if dist < min_distance:
                min_distance = dist
                location_name = f"Near {loc['name']}"
    else:
        # Fallback if no MQTT data is available
        current_lat = efarming_location["lat"]
        current_lon = efarming_location["lon"]
        location_name = "eFarming Corpora Community"
    
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
    
    # Add path history (last few points)
    # history_length = min(10, len(data["kodeDataLat"]))
    # if history_length > 1:
    #     # Get the last few GPS points from the MQTT data
    #     path_lats = data["kodeDataLat"][-history_length:]
    #     path_lons = data["kodeDataLon"][-history_length:]
        
    #     fig.add_trace(go.Scattermapbox(
    #         lat=path_lats,
    #         lon=path_lons,
    #         mode='lines',
    #         line=dict(width=2, color='orange'),
    #         name="Device Path"
    #     ))
    
    # Configure the map layout
    fig.update_layout(
        mapbox=dict(
            style="open-street-map",
            center=dict(lat=current_lat, lon=current_lon),  # Center on current coordinates
            zoom=15,  # Default zoom level (slightly zoomed in)
            uirevision=f"{current_lat}_{current_lon}"  # Preserve zoom level while centered on current point
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
     Output("rainfall-circle", "className")],
    [Input("interval-alarm", "n_intervals")]
)
def update_alarm_values(n):
    def get_circle_class(kode_alarm):
        if kode_alarm in [1, 4]:
            return "status-circle status-red"
        elif kode_alarm in [2, 3]:
            return "status-circle status-yellow"
        else:  # kode_alarm == 0
            return "status-circle status-green"
    
    return (
        alarm_data['kodeAlarmSuhuIn'],
        alarm_data['beritaSuhuIn'],
        get_circle_class(alarm_data['kodeAlarmSuhuIn']),
        alarm_data['kodeAlarmKelembabanIn'],
        alarm_data['beritaKelembabanIn'],
        get_circle_class(alarm_data['kodeAlarmKelembabanIn']),
        alarm_data['kodeAlarmSuhuOut'],
        alarm_data['beritaSuhuOut'],
        get_circle_class(alarm_data['kodeAlarmSuhuOut']),
        alarm_data['kodeAlarmKelembabanOut'],
        alarm_data['beritaKelembabanOut'],
        get_circle_class(alarm_data['kodeAlarmKelembabanOut']),
        alarm_data['kodeAlarmPar'],
        alarm_data['beritaPar'],
        get_circle_class(alarm_data['kodeAlarmPar']),
        alarm_data['kodeAlarmCo2'],
        alarm_data['beritaCo2'],
        get_circle_class(alarm_data['kodeAlarmCo2']),
        alarm_data['kodeAlarmWindspeed'],
        alarm_data['beritaWindspeed'],
        get_circle_class(alarm_data['kodeAlarmWindspeed']),
        alarm_data['kodeAlarmRainfall'],
        alarm_data['beritaRainfall'],
        get_circle_class(alarm_data['kodeAlarmRainfall'])
    )

# Run server
if __name__ == '__main__':
    server.run(server.run(host='0.0.0.0', port=5000))
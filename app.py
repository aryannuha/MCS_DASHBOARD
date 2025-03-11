import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import paho.mqtt.client as mqtt
import pandas as pd
import plotly.graph_objs as go
import threading
import requests

# Inisialisasi Dash
app = dash.Dash(__name__, external_stylesheets=['/assets/style.css'], title="Dashboard Microclimate")
server = app.server

# Data Storage
data = {'waktu': [], 'suhu': [], 'kelembaban': []}

# Google Sheets Configuration
apps_script_url = "https://script.google.com/macros/s/AKfycbyazZJNxu7Pa7ZuYzwAW2zJHXq30Jb48yZSKizD4c_RxDInRvKuOOWWwqCz5d1RT-ShlA/exec?mode=read"

# MQTT Configuration
BROKER = "9a59e12602b646a292e7e66a5296e0ed.s1.eu.hivemq.cloud"
PORT = 8883
USERNAME = "testing"
PASSWORD = "Testing123"
TOPIC_SUHU = "esp32/suhu"
TOPIC_KELEMBABAN = "esp32/kelembaban"

# MQTT Callback
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to HiveMQ Broker")
        client.subscribe([(TOPIC_SUHU, 0), (TOPIC_KELEMBABAN, 0)])  # Subscribe ke topik suhu & kelembaban
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    global data
    # print(f"Received message: {msg.topic} - {msg.payload.decode()}")
    try:
        value = float(msg.payload.decode())
        time = pd.Timestamp.now().strftime('%H:%M:%S')
        if msg.topic == TOPIC_SUHU:
            data['waktu'].append(time)
            data['suhu'].append(value)
        elif msg.topic == TOPIC_KELEMBABAN:
            data['kelembaban'].append(value)
        
        if len(data['waktu']) > 20:
            data['waktu'].pop(0)
            data['suhu'].pop(0)
            data['kelembaban'].pop(0)
    
    except Exception as e:
        print(f"Error processing MQTT message: {e}")

# MQTT Client
client = mqtt.Client()
client.username_pw_set(USERNAME, PASSWORD)
client.tls_set()
client.on_connect = on_connect
client.on_message = on_message
client.connect(BROKER, PORT, 60)

# Jalankan MQTT dalam thread
threading.Thread(target=client.loop_forever, daemon=True).start()

# Layout Dashboard
app.layout = html.Div([
    html.H1("DASHBOARD MONITORING MICROCLIMATE"),

    html.Div([
        # Bagian kiri
        html.Div([
            html.Div([
                html.Img(src='/assets/img/thermometer.png', className='icon'),
                html.Div(id='suhu-display', className='data-box')
            ],className='data-item'),

            html.Div([
                html.Img(src='/assets/img/humidity.png', className='icon'),
                html.Div(id='kelembaban-display', className='data-box')
            ],className='data-item'),

            html.Div([
                html.Table([
                    html.Thead([
                        html.Tr([html.Th("Waktu"), html.Th("Suhu (°C)"), html.Th("Kelembaban (%)")])
                    ]),
                    html.Tbody(id='table-body')
                ], className='data-table'),
            ], className='table-container'),

            html.Button("Historical Trend", id='btn-his', className='btn-his'),

            html.Button("Move to PAR", id='btn-par', className='btn-par'),
        ], className='left-panel'),

        # Bagian kanan (grafik)
        html.Div([
            dcc.Graph(id='suhu-graph', className='grafik'),
            dcc.Graph(id='kelembaban-graph', className='grafik'),
        ], className='right-panel'),

    ], className='main-container'),

    # Historical Trend Modal
    html.Div([
        html.Div([
            html.H2("Historical Trend"),
            dcc.Dropdown(
                id='filter-dropdown',
                options=[
                    {'label': 'Jam', 'value': 'hour'},
                    {'label': 'Hari', 'value': 'day'},
                    {'label': 'Minggu', 'value': 'week'},
                    {'label': 'Bulan', 'value': 'month'}
                ],
                value='hour'
            ),
            dcc.Graph(id='historical-graph'),
            html.Button("Close", id='close-modal', className='close-btn')
        ], className='modal-content')
    ], id='modal', className='modal', style={'display': 'none'}),

    dcc.Interval(id='interval', interval=2000, n_intervals=0)
])

# Callback Historical Trend
@app.callback(
    Output('modal', 'style'),
    [Input('btn-his', 'n_clicks'), Input('close-modal','n_clicks')],
    [State('modal','style')]
)

# Pop up modal
def toggle_modal(btn_open, btn_close, style):
    ctx = dash.callback_context
    if not ctx.triggered:
        return style
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if trigger_id == 'btn-his':
        return {'display': 'block'}
    return {'display': 'none'}

# Callback update historical graph
@app.callback(
    Output('historical-graph', 'figure'),
    [Input('filter-dropdown', 'value')]
)

# Update historical trend
def update_historical_graph(filter_value):
    try:
        response = requests.get(apps_script_url)

        # print("Status Code:", response.status_code)
        # print("Response JSON:", response.text)  # Debugging

        if response.status_code != 200:
            print("Error: Tidak dapat mengambil data dari Google Sheets.")
            return go.Figure()

        sheet_data = response.json()
        if not sheet_data:
            print("Warning: Data dari Google Sheets kosong.")
            return go.Figure()

        # **Konversi ke DataFrame**
        df = pd.DataFrame(sheet_data)

        # print("Dataframe setelah diambil dari Google Sheets:")
        # print(df.head())  # Debugging

        # **Bersihkan header & strip whitespace**
        df.columns = df.columns.str.strip()
        df = df.apply(lambda x: x.map(str.strip) if x.dtype == "object" else x)

        # **Konversi Date dengan format yang sesuai**
        df['Timestamp'] = pd.to_datetime(df['Date'], utc=True, errors='coerce')
        df['Timestamp'] = df['Timestamp'].dt.tz_convert('Asia/Jakarta')

        # **Cek Timestamp unik setelah konversi**
        # print("Timestamp unik setelah konversi:")
        # print(df['Timestamp'].unique())

        # **Buang baris dengan Timestamp yang NaT**
        df = df.dropna(subset=['Timestamp'])
        # print("Jumlah data setelah drop NaT:", len(df))

        # **Filter berdasarkan pilihan pengguna**
        now = pd.Timestamp.now(tz='Asia/Jakarta')
        filter_map = {
            'hour': pd.Timedelta(hours=1),
            'day': pd.Timedelta(days=1),
            'week': pd.Timedelta(weeks=1),
            'month': pd.Timedelta(weeks=4)
        }

        if filter_value in filter_map:
            filter_time = now - filter_map[filter_value]
            # print(f"Filter dari: {filter_time}")
            df = df[df['Timestamp'] < filter_time]

        # print("Jumlah data setelah filter:", len(df))
        
        if df.empty:
            print("Warning: Tidak ada data setelah filter. Grafik tidak akan muncul.")
            return go.Figure()

        # **Validasi kolom suhu dan kelembaban**
        rename_map = {'Temp (°C)': 'suhu', 'Humidity (%)': 'kelembaban'}
        missing_cols = [col for col in rename_map.keys() if col not in df.columns]

        if missing_cols:
            print(f"Error: Kolom {missing_cols} tidak ditemukan dalam data.")
            return go.Figure()

        df = df.rename(columns=rename_map)

        # **Buat grafik**
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['suhu'], mode='lines+markers', name='Suhu'))
        fig.add_trace(go.Scatter(x=df['Timestamp'], y=df['kelembaban'], mode='lines+markers', name='Kelembaban'))
        fig.update_layout(title='Historical Trend', xaxis_title='Time', yaxis_title='Nilai')

        return fig

    except requests.exceptions.RequestException as e:
        print(f"Request Error: {e}")
        return go.Figure()
    except Exception as e:
        print(f"Error saat memproses data: {e}")
        return go.Figure()

# Callback Real Time Trend
@app.callback(
    [Output('suhu-display', 'children'),
     Output('kelembaban-display', 'children'),
     Output('suhu-graph', 'figure'),
     Output('kelembaban-graph', 'figure'),
     Output('table-body', 'children')],
    [Input('interval', 'n_intervals')]
)

# update dashboard Real Time Trend
def update_dashboard(n):
    suhu = data['suhu'][-1] if len(data['suhu']) == len(data['waktu']) and data['suhu'] else 0
    kelembaban = data['kelembaban'][-1] if len(data['kelembaban']) == len(data['waktu']) and data['kelembaban'] else 0

    suhu_display = f"Suhu Udara: {suhu}°C"
    kelembaban_display = f"Kelembapan Udara: {kelembaban}%"
    
    fig_suhu = go.Figure(go.Scatter(x=data['waktu'], y=data['suhu'], mode='lines+markers', name='suhu'))
    fig_suhu.update_layout(title='Suhu Udara', xaxis_title='Waktu', yaxis_title='Suhu (°C)')
    
    fig_kelembaban = go.Figure(go.Scatter(x=data['waktu'], y=data['kelembaban'], mode='lines+markers', name='kelembaban'))
    fig_kelembaban.update_layout(title='Kelembaban Udara', xaxis_title='Waktu', yaxis_title='Kelembaban (%)')
    
    table_rows = [html.Tr([html.Td(w), html.Td(s), html.Td(k)]) 
              for w, s, k in zip(data['waktu'], data['suhu'], data['kelembaban'])]
    
    return suhu_display, kelembaban_display, fig_suhu, fig_kelembaban, table_rows

if __name__ == '__main__':
    app.run_server(debug=True)

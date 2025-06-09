''' 
 Nama File      : alarm_eng.py
 Tanggal Update : 09 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
    1. Membuat layout untuk halaman Alarm Dashboard
    2. Menggunakan komponen Dash dan Bootstrap untuk tata letak yang responsif
    3. Menyediakan parameter sensor dalam bentuk kartu
    4. Menyediakan tombol navigasi untuk halaman lain
    5. Menggunakan interval untuk pembaruan data secara berkala
'''

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

# Alarm Dashboard Layout
engineer_alarm_layout = html.Div([
     # NAVBAR
    html.Div([
        html.Div(html.Img(src="/static/img/lpdp.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/diktisaintekdan.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/ipb.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polsub.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polindra.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polban.png", className="navbar-logo")),
        html.Div("ALARM DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full"),

    # PARAMETER CARDS - ROW 1
    html.Div([
        # Temperature In
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Temperature In (°C)", className="param-title"),
                    html.Div(id="temp-in-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="temp-in-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="temp-in-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # Humidity In
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Humidity In (%)", className="param-title"),
                    html.Div(id="humidity-in-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="humidity-in-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="humidity-in-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # Temperature Out
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Temperature Out (°C)", className="param-title"),
                    html.Div(id="temp-out-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="temp-out-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="temp-out-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
    ], className="row mx-1 mt-3"),
    
    # PARAMETER CARDS - ROW 2
    html.Div([
        # Humidity Out
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Humidity Out (%)", className="param-title"),
                    html.Div(id="humidity-out-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="humidity-out-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="humidity-out-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # PAR
        html.Div([
            html.Div([
                html.Div([
                    html.H5("PAR (μmol/m²/s)", className="param-title"),
                    html.Div(id="par-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="par-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="par-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # CO2
        html.Div([
            html.Div([
                html.Div([
                    html.H5("CO2 (PPM)", className="param-title"),
                    html.Div(id="co2-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="co2-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="co2-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
    ], className="row mx-1"),
    
    # PARAMETER CARDS - ROW 3
    html.Div([
        # Windspeed
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Windspeed (m/s)", className="param-title"),
                    html.Div(id="windspeed-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="windspeed-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="windspeed-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # Rainfall
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Rainfall (mm)", className="param-title"),
                    html.Div(id="rainfall-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="rainfall-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="rainfall-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),

        # Voltage AC
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Voltage AC (V)", className="param-title"),
                    html.Div(id="voltage-ac-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="voltage-ac-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="voltage-ac-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
    ], className="row mx-1"),

    # PARAMETER CARDS - ROW 4
    html.Div([
        # Current AC
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Current AC (A)", className="param-title"),
                    html.Div(id="current-ac-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="current-ac-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="current-ac-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),

        # Power AC
        html.Div([
            html.Div([
                html.Div([
                    html.H5("Power AC (W)", className="param-title"),
                    html.Div(id="power-ac-circle", className="status-circle")
                ], className="title-with-circle"),
                html.Div([
                    html.Div([
                        html.Strong("kodeAlarm:", className="me-2"),
                        html.Span(id="power-ac-alarm", children="0")
                    ], className="d-flex justify-content-between"),
                    html.Div([
                        html.Strong("berita:", className="me-2"),
                        html.Span(id="power-ac-berita", children="Normal")
                    ], className="d-flex justify-content-between")
                ])
            ], className="param-card")
        ], className="col-md-4 mb-3"),
        
        # Button Section
        html.Div([
            # html.Button("SETTING", className="btn btn-secondary m-1"),
            dcc.Link("MCS", href="/dash/", className="btn btn-secondary m-1"),
            dcc.Link("T&H INDOOR", href="/dash/th-in", className="btn btn-secondary m-1"),
            dcc.Link("PAR", href="/dash/par", className="btn btn-secondary m-1"),
            dcc.Link("CO2", href="/dash/co2", className="btn btn-secondary m-1"),
            dcc.Link("T&H OUTDOOR", href="/dash/th-out", className="btn btn-secondary m-1"),
            dcc.Link("WINDSPEED", href="/dash/windspeed", className="btn btn-secondary m-1"),
            dcc.Link("RAINFALL", href="/dash/rainfall", className="btn btn-secondary m-1"),
            html.Button("LOGIN", id="login-button", className="btn btn-dark m-1"),
            dcc.Location(id="login-redirect", refresh=True)  # Handles redirection
        ], className="d-flex flex-wrap justify-content-end mb-4")
        
        # Empty card or additional parameter if needed
        # html.Div([
            # This div can be left empty or used for an additional parameter
        # ], className="col-md-4 mb-3"),
    ], className="row mx-1"),
    
    # Interval for updating the alarms
    dcc.Interval(id='interval-alarm', interval=1200, n_intervals=0)
])
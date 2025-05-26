from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

# Alarm Dashboard Layout
engineer_alarm_layout = html.Div([
     # NAVBAR
    html.Div([
        html.Div("ALARM DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full"),

    # PARAMETER CARDS - ROW 1
    html.Div([
        # Temperature In
        html.Div([
            html.Div([
                html.H5("Temperature In (°C)", className="param-title"),
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
                html.H5("Humidity In (%)", className="param-title"),
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
                html.H5("Temp Out (°C)", className="param-title"),
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
                html.H5("Humidity Out (%)", className="param-title"),
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
                html.H5("PAR (μmol/m²/s)", className="param-title"),
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
                html.H5("CO2 (PPM)", className="param-title"),
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
                html.H5("Windspeed (m/s)", className="param-title"),
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
                html.H5("Rainfall (mm)", className="param-title"),
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
        
        # Button Section
        html.Div([
            html.Button("SETTING", className="btn btn-secondary m-1"),
            dcc.Link("MCS", href="/dash/engineer/", className="btn btn-secondary m-1"),
            dcc.Link("T&H INDOOR", href="/dash/engineer/th-in", className="btn btn-secondary m-1"),
            dcc.Link("PAR", href="/dash/engineer/par", className="btn btn-secondary m-1"),
            dcc.Link("CO2", href="/dash/engineer/co2", className="btn btn-secondary m-1"),
            dcc.Link("T&H OUTDOOR", href="/dash/engineer/th-out", className="btn btn-secondary m-1"),
            dcc.Link("WINDSPEED", href="/dash/engineer/windspeed", className="btn btn-secondary m-1"),
            dcc.Link("RAINFALL", href="/dash/engineer/rainfall", className="btn btn-secondary m-1"),
            html.Button("LOGOUT", id="logout-button", className="btn btn-dark m-1"),
            dcc.Location(id="logout-redirect", refresh=True)  # Handles redirection
        ], className="d-flex flex-wrap justify-content-end mb-4")
        
        # Empty card or additional parameter if needed
        # html.Div([
            # This div can be left empty or used for an additional parameter
        # ], className="col-md-4 mb-3"),
    ], className="row mx-1"),
    
    # Interval for updating the alarms
    dcc.Interval(id='interval-alarm', interval=1200, n_intervals=0)
])
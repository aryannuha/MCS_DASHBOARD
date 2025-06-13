''' 
 Nama File      : mcs_dashboard_eng.py
 Tanggal Update : 09 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
   1. Membuat layout utama untuk dashboard sistem mikroklimat.
   2. Menggunakan komponen Dash dan Bootstrap untuk tata letak yang responsif.
'''

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

# IP WebServer
ESP_IP = "http://192.168.0.240"

engineer_dashboard_layout = html.Div([
    # NAVBAR
    html.Div([
        html.Div(html.Img(src="/static/img/lpdp.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/diktisaintekdan.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/ipb.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polsub.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polindra.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polban.png", className="navbar-logo")),
        html.Div("MICROCLIMATE SYSTEM DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full"),

    # TAMPILAN PARAMETER SENSOR GRID
    html.Div([
        dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.Div([
                        html.Img(src="/static/icon/temperature.svg", className="param-icon me-2"),
                        html.Span("TEMPERATURE IN", className="param-title me-2"),
                        html.Span(id={'type': 'sensor-value', 'id': 'suhu-display-indoor'}, className="param-value")
                    ], className="d-flex align-items-center mb-2"),
                    html.Div([
                        html.Img(src="/static/icon/humidity.svg", className="param-icon me-2"),
                        html.Span("HUMIDITY IN", className="param-title me-2"),
                        html.Span(id={'type': 'sensor-value', 'id': 'kelembaban-display-indoor'}, className="param-value")
                    ], className="d-flex align-items-center")
                ])
            ], className="param-card"), width=4),

            dbc.Col(html.Div([
                html.Div([
                    html.Img(src="/static/icon/sun.svg", className="param-icon me-2"),
                    html.Span("PAR", className="param-title me-2"),
                    html.Span(id={'type': 'sensor-value', 'id': 'par-display'}, className="param-value")
                ], className="d-flex align-items-center")
            ], className="param-card"), width=4),

            dbc.Col(html.Div([
                html.Div([
                    html.Img(src="/static/icon/co.svg", className="param-icon me-2"),
                    html.Span("CO2", className="param-title me-2"),
                    html.Span(id={'type': 'sensor-value', 'id': 'co2-display'}, className="param-value")
                ], className="d-flex align-items-center")
            ], className="param-card"), width=4),
        ], className="mb-3"),

        dbc.Row([
            dbc.Col(html.Div([
                html.Div([
                    html.Div([
                        html.Img(src="/static/icon/temperature.svg", className="param-icon me-2"),
                        html.Span("TEMPERATURE OUT", className="param-title me-2"),
                        html.Span(id={'type': 'sensor-value', 'id': 'suhu-display-outdoor'}, className="param-value")
                    ], className="d-flex align-items-center mb-2"),
                    html.Div([
                        html.Img(src="/static/icon/humidity.svg", className="param-icon me-2"),
                        html.Span("HUMIDITY OUT", className="param-title me-2"),
                        html.Span(id={'type': 'sensor-value', 'id': 'kelembaban-display-outdoor'}, className="param-value")
                    ], className="d-flex align-items-center")
                ])
            ], className="param-card"), width=4),

            dbc.Col(html.Div([
                html.Div([
                    html.Img(src="/static/icon/windspeed.svg", className="param-icon me-2"),
                    html.Span("WINDSPEED", className="param-title me-2"),
                    html.Span(id={'type': 'sensor-value', 'id': 'windspeed-display'}, className="param-value")
                ], className="d-flex align-items-center")
            ], className="param-card"), width=4),

            dbc.Col(html.Div([
                html.Div([
                    html.Img(src="/static/icon/rainfall.svg", className="param-icon me-2"),
                    html.Span("RAINFALL", className="param-title me-2"),
                    html.Span(id={'type': 'sensor-value', 'id': 'rainfall-display'}, className="param-value")
                ], className="d-flex align-items-center")
            ], className="param-card"), width=4),
        ])
    ], className="container"),

    # TAMPILAN BOTTOM GRID
    html.Div([
        dbc.Row([
            dbc.Col(html.Img(src="/static/img/pictogram_mcs_3.png", className="greenhouse-img"), width=6),
            dbc.Col([
                # Table Section
                html.Div([
                    html.H4("Real Time Table", className="text-center mb-2"),
                    dash_table.DataTable(
                        id='realtime-table',
                        columns=[
                            {"name": i, "id": i} for i in [
                                "Time", "Temp In (°C)", "Humidity In (%)", "Temp Out (°C)", "Humidity Out (%)", 
                                "PAR (μmol/m²/s)", "CO2 (PPM)", "Windspeed (m/s)", "Rainfall (mm)",
                                "Voltage AC (V)", "Current AC (A)", "Power AC (W)"
                            ]
                        ],
                        data=[],
                        style_table={
                            'overflowX': 'auto',    # Horizontal scrolling if needed
                            'overflowY': 'auto',    # Enable vertical scrolling
                            'height': '220px'       # Increased height for better visibility
                        },
                        style_cell={"textAlign": "center"},
                        style_data_conditional=[
                            {
                                'if': {'row_index': 0},
                                'backgroundColor': '#EFEFEF',
                                'fontWeight': 'bold'
                            }
                        ],
                        # page_action='none',  # Disable pagination
                        # fixed_rows={'headers': True},  # Keep headers visible when scrolling
                    )
                ], className="data-table mb-3"),

                # Button Section
                html.Div([
                    # html.Button("SETTING", className="btn btn-secondary m-1"),
                    html.A("DOWNLOAD", href=f"{ESP_IP}/download", className="btn btn-secondary m-1", target="_blank"),
                    dcc.Link("T&H INDOOR", href="/dash/engineer/th-in", className="btn btn-secondary m-1"),
                    dcc.Link("PAR", href="/dash/engineer/par", className="btn btn-secondary m-1"),
                    dcc.Link("CO2", href="/dash/engineer/co2", className="btn btn-secondary m-1"),
                    dcc.Link("T&H OUTDOOR", href="/dash/engineer/th-out", className="btn btn-secondary m-1"),
                    dcc.Link("WINDSPEED", href="/dash/engineer/windspeed", className="btn btn-secondary m-1"),
                    dcc.Link("RAINFALL", href="/dash/engineer/rainfall", className="btn btn-secondary m-1"),
                    dcc.Link("EPS", href="/dash/engineer/eps", className="btn btn-secondary m-1"),
                    html.Button("LOGOUT", id="logout-button", className="btn btn-dark m-1"),
                    dcc.Location(id="logout-redirect", refresh=True)  # Handles redirection
                ], className="d-flex flex-wrap justify-content-end")
            ], width=6)
        ], className="g-2")
    ], className="container mb-5"),

    # FOOTER
    html.Footer([
        html.Div([
            html.P([
                "© Ammar Aryan Nuha 221311008 • Created with ",
                html.Span("♥", className="love-symbol"),
                " for Microclimate System"
            ], className="footer-text mb-0")
        ], className="container text-center")
    ], className="footer-section"),

    dcc.Interval(id='interval_mcs', interval=1200, n_intervals=0)
])
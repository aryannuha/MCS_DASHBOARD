''' 
 Nama File      : windspeed_eng.py
 Tanggal Update : 09 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
    1. Membuat layout untuk halaman Windspeed Dashboard
    2. Menggunakan komponen Dash dan Bootstrap untuk tata letak yang responsif
    3. Menyediakan grafik real-time, prediksi, dan tabel historis
    4. Menyediakan tombol navigasi untuk halaman lain
    5. Menggunakan interval untuk pembaruan data secara berkala
'''

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

engineer_windspeed_layout = html.Div([
    # NAVBAR
    html.Div([
        html.Div(html.Img(src="/static/img/lpdp.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/diktisaintekdan.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/ipb.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polsub.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polindra.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polban.png", className="navbar-logo")),
        html.Div("WINDSPEED DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full mb-1"),
    
    # MAIN CONTENT
    html.Div([
        dbc.Row([
            # LEFT SIDE - Parameter Cards and Greenhouse Image
            dbc.Col([
                # Windspeed in a row
                dbc.Row([
                    # Windspeed Card
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/windspeed.svg", className="param-icon me-2"),
                            html.H5("WINDSPEED", className="mb-2"),
                            html.H3(id={'type': 'sensor-value', 'id': 'windspeed-display'}, className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=12),
                ], className="mb-3"),
                
                # WINDSPEED Prediction Graph Section
                html.Div([
                    html.H5("WINDSPEED PREDICTION (1-5 Minutes)", className="text-center mb-3"),
                    
                    # WINDSPEED Prediction Graph
                    html.Div([
                        html.H6("WINDSPEED Prediction", className="text-center mb-2"),
                        dcc.Graph(
                            id='windspeed-prediction-graph',
                            config={"displayModeBar": False},
                            style={'height': '258px'}
                        )
                    ], className="mb-3 p-2 border rounded bg-light"),
                ], className="prediction-container")
            ], width=6, className="pe-3"),
            
           # RIGHT SIDE - Graphs and Table
                dbc.Col([
                    # Real-time Trend Graphs with clear IDs and sufficient height
                    html.Div([
                        html.H5("REAL-TIME TREND", className="text-center mb-2"),
                        
                        # Windspeed Graph - Using a simple div wrapper
                        html.Div([
                            dcc.Graph(
                                id='windspeed-graph',
                                config={"displayModeBar": False},
                                style={'height': '300px'}
                            )
                        ]), 
                    ], className="mb-3 p-2 border rounded bg-light"),
                
                # Historical Data Table
                html.Div([
                    html.H5("HISTORICAL TABLE", className="text-center mb-2"),
                    dash_table.DataTable(
                        id='historical-table-windspeed',
                        columns=[
                            {"name": "Time (m)", "id": "time"},
                            {"name": "Windspeed (m/s)", "id": "windspeed-historical"},
                        ],
                        data=[
                            # Empty rows for demonstration
                            {} for _ in range(2)
                        ],
                        style_table={'overflowX': 'auto',    # Horizontal scrolling if needed
                            'overflowY': 'auto',    # Enable vertical scrolling
                            'height': '102px'       # Increased height for better visibility
                        },
                        style_cell={'textAlign': 'center', 'padding': '5px'},
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        style_data_conditional=[
                            {
                                'if': {'row_index': 'odd'},
                                'backgroundColor': '#f8f9fa'
                            }
                        ]
                    )
                ], className="mb-3 p-2 border rounded bg-light"),
                
                # Buttons
                html.Div([
                    # html.Button("SETTING", className="btn btn-secondary m-1"),
                    dcc.Link("MCS", href="/dash/engineer/", className="btn btn-secondary m-1"),
                    dcc.Link("PAR", href="/dash/engineer/par", className="btn btn-secondary m-1"),
                    dcc.Link("CO2", href="/dash/engineer/co2", className="btn btn-secondary m-1"),
                    dcc.Link("T&H INDOOR", href="/dash/engineer/th-in", className="btn btn-secondary m-1"),
                    dcc.Link("T&H OUTDOOR", href="/dash/engineer/th-out", className="btn btn-secondary m-1"),
                    dcc.Link("RAINFALL", href="/dash/engineer/rainfall", className="btn btn-secondary m-1"),
                    dcc.Link("EPS", href="/dash/engineer/eps", className="btn btn-secondary m-1"),
                    html.Button("LOGOUT", id="logout-button", className="btn btn-dark m-1"),
                    dcc.Location(id="logout-redirect", refresh=True)  # Handles redirection
                ], className="d-flex justify-content-end")
            ], width=6, className="ps-3")
        ])
    ], className="container"),

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
    
    # Keep the interval component for data updates
    dcc.Interval(id='interval_windspeed', interval=3000, n_intervals=0)
])
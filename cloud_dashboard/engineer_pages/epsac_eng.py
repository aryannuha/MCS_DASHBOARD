''' 
 Nama File      : eps_ac.py
 Tanggal Update : 13 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
    1. Membuat layout untuk halaman EPS AC
    2. Menggunakan komponen Dash dan Bootstrap untuk tata letak yang responsif
    3. Menyediakan grafik real-time dan tabel historis untuk parameter AC
    4. Menyediakan tombol navigasi untuk halaman lain
    5. Menggunakan interval untuk pembaruan data secara berkala
'''

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

engineer_eps_ac_layout = html.Div([
    # NAVBAR
    html.Div([
        html.Div(html.Img(src="/static/img/lpdp.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/diktisaintekdan.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/ipb.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polsub.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polindra.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polban.png", className="navbar-logo")),
        html.Div("EPS AC DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full mb-1"),
    
    # MAIN CONTENT
    html.Div([
        dbc.Row([
            # LEFT SIDE - Parameter Cards
            dbc.Col([
                # Voltage and Current Cards in a row
                dbc.Row([
                    # Voltage Card
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/voltage.svg", className="param-icon me-2"),
                            html.H5("VOLTAGE AC", className="mb-2"),
                            html.H3(id="voltage-ac-display", className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=6),
                    
                    # Current Card
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/current.svg", className="param-icon me-2"),
                            html.H5("CURRENT AC", className="mb-2"),
                            html.H3(id="current-ac-display", className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=6),
                ], className="mb-3"),
                
                # Power Card (full width)
                dbc.Row([
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/power.svg", className="param-icon me-2"),
                            html.H5("POWER AC", className="mb-2"),
                            html.H3(id="power-ac-display", className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=12),
                ], className="mb-3"),
                
                # Voltage AC Graph (moved from right side)
                html.Div([
                    html.H5("HISTORICAL TABLE", className="text-center mb-2"),
                    dash_table.DataTable(
                        id='historical-table-eps-ac',
                        columns=[
                            {"name": "Time (m)", "id": "time"},
                            {"name": "Voltage AC (V)", "id": "voltage_ac_historical"},
                            {"name": "Current AC (A)", "id": "current_ac_historical"},
                            {"name": "Power AC (W)", "id": "power_ac_historical"}
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
                
            ], width=6, className="pe-3"),
            
           # RIGHT SIDE - Graphs and Table
                dbc.Col([
                    # Real-time Trend Graphs with clear IDs and sufficient height
                    html.Div([
                        html.H5("REAL-TIME TREND", className="text-center mb-2"),
                        
                        # Voltage AC Graph
                        html.Div([
                            dcc.Graph(
                                id='voltage-ac-graph',
                                config={"displayModeBar": False},
                                style={'height': '190px'}
                            )
                        ]),

                        # Current Graph
                        html.Div([
                            dcc.Graph(
                                id='current-ac-graph',
                                config={"displayModeBar": False},
                                style={'height': '190px'}
                            )
                        ]),
                        
                        # Power Graph
                        html.Div([
                            dcc.Graph(
                                id='power-ac-graph',
                                config={"displayModeBar": False},
                                style={'height': '190px'}
                            )
                        ]), 
                    ], className="mb-3 p-2 border rounded bg-light"),
                
                # Navigation Buttons
                html.Div([
                    dcc.Link("MCS", href="/dash/engineer/", className="btn btn-secondary m-1"),
                    dcc.Link("PAR", href="/dash/engineer/par", className="btn btn-secondary m-1"),
                    dcc.Link("CO2", href="/dash/engineer/co2", className="btn btn-secondary m-1"),
                    dcc.Link("T&H INDOOR", href="/dash/engineer/th-in", className="btn btn-secondary m-1"),
                    dcc.Link("T&H OUTDOOR", href="/dash/engineer/th-out", className="btn btn-secondary m-1"),
                    dcc.Link("WINDSPEED", href="/dash/engineer/windspeed", className="btn btn-secondary m-1"),
                    dcc.Link("RAINFALL", href="/dash/engineer/rainfall", className="btn btn-secondary m-1"),
                    html.Button("LOGOUT", id="logout-button", className="btn btn-dark m-1"),
                    dcc.Location(id="logout-redirect", refresh=True)  # Handles redirection
                ], className="d-flex flex-wrap justify-content-end")
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
    dcc.Interval(id='interval_eps_ac', interval=3000, n_intervals=0)
])
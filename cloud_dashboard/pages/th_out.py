from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

th_out_layout = html.Div([
    # NAVBAR
    html.Div([
        html.Div("T&H OUTDOOR DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full mb-1"),
    
    # MAIN CONTENT
    html.Div([
        dbc.Row([
            # LEFT SIDE - Parameter Cards and Greenhouse Image
            dbc.Col([
                # Temperature and Humidity Cards in a row
                dbc.Row([
                    # Temperature Card
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/temperature.svg", className="param-icon me-2"),
                            html.H5("TEMPERATURE", className="mb-2"),
                            html.H3(id={'type': 'sensor-value', 'id': 'suhu-display-outdoor'}, className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=6),
                    
                    # Humidity Card
                    dbc.Col(
                        html.Div([
                            html.Img(src="/static/icon/humidity.svg", className="param-icon me-2"),
                            html.H5("HUMIDITY", className="mb-2"),
                            html.H3(id={'type': 'sensor-value', 'id': 'kelembaban-display-outdoor'}, className="fw-bold")
                        ], className="parameter-card p-3 h-100 border rounded"),
                    width=6),
                ], className="mb-3"),
                
                # Greenhouse Image
                html.Div([
                    html.Img(src="/static/img/gh.jpg", className="img-fluid w-100 border border-primary p-1", 
                            style={"height": "300px", "object-fit": "cover"})
                ], className="greenhouse-container")
            ], width=6, className="pe-3"),
            
           # RIGHT SIDE - Graphs and Table
                dbc.Col([
                    # Real-time Trend Graphs with clear IDs and sufficient height
                    html.Div([
                        html.H5("REAL-TIME TREND", className="text-center mb-2"),
                        
                        # Temperature Graph - Using a simple div wrapper
                        html.Div([
                            dcc.Graph(
                                id='temp-graph-out',
                                config={"displayModeBar": False},
                                style={'height': '150px'}
                            )
                        ]), 
                        
                        # Humidity Graph - Using a simple div wrapper
                        html.Div([
                            dcc.Graph(
                                id='humidity-graph-out',
                                config={"displayModeBar": False},
                                style={'height': '150px'}
                            )
                        ]), 
                    ], className="mb-3 p-2 border rounded bg-light"),
                
                # Historical Data Table
                html.Div([
                    html.H5("HISTORICAL TABLE", className="text-center mb-2"),
                    dash_table.DataTable(
                        id='historical-table-th-out',
                        columns=[
                            {"name": "Time (h)", "id": "time"},
                            {"name": "Temperature (°C)", "id": "temperature_out_historical"},
                            {"name": "Humidity (%)", "id": "humidity_out_historical"}
                        ],
                        data=[
                            # Empty rows for demonstration
                            {} for _ in range(2)
                        ],
                        style_table={'overflowX': 'auto'},
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
                    dcc.Link("MCS", href="/dash/", className="btn btn-secondary m-1"),
                    dcc.Link("PAR", href="/dash/par", className="btn btn-secondary m-1"),
                    dcc.Link("CO2", href="/dash/co2", className="btn btn-secondary m-1"),
                    dcc.Link("T&H INDOOR", href="/dash/th-in", className="btn btn-secondary m-1"),
                    dcc.Link("WINDSPEED", href="/dash/windspeed", className="btn btn-secondary m-1"),
                    dcc.Link("RAINFALL", href="/dash/rainfall", className="btn btn-secondary m-1"),
                    html.Button("LOGIN", id="login-button", className="btn btn-dark m-1"),
                    dcc.Location(id="login-redirect", refresh=True)  # Handles redirection
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
    dcc.Interval(id='interval_thout', interval=1200, n_intervals=0)
])
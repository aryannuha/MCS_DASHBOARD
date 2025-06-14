''' 
 Nama File      : gps_eng.py
 Tanggal Update : 09 Juni 2025
 Dibuat oleh    : Ammar Aryan Nuha
 Penjelasan     : 
    1. Membuat layout untuk halaman GPS Dashboard
    2. Menggunakan komponen Dash dan Bootstrap untuk tata letak yang responsif
    3. Menyediakan peta interaktif dengan data GPS
    4. Menampilkan informasi lokasi dan koordinat saat ini
    5. Menyediakan tombol navigasi untuk halaman lain
    6. Menggunakan interval untuk pembaruan data secara berkala
'''

from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

# GPS DASHBOARD LAYOUT
engineer_gps_layout = html.Div([
    # NAVBAR
    html.Div([
        html.Div(html.Img(src="/static/img/lpdp.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/diktisaintekdan.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/ipb.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polsub.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polindra.png", className="navbar-logo")),
        html.Div(html.Img(src="/static/img/polban.png", className="navbar-logo")),
        html.Div("GPS DASHBOARD", className="navbar-title"),
        dcc.Link(html.Img(src="/static/icon/gps.svg", className="gps-icon me-2"), href="/dash/engineer/gps"),
        dcc.Link(html.Img(src="/static/icon/notification.svg", className="notification-icon"), href="/dash/engineer/alarm"),
    ], className="d-flex justify-content-between align-items-center p-3 border-bottom navbar-full"),
    
    # MAIN CONTENT
    html.Div([
        # Map Section
        html.Div([
            # Map Container
            html.Div([
                dcc.Graph(
                    id='gps-map',
                    figure={
                        'data': [],  # Empty data initially, will be populated by callbacks
                        'layout': {
                            'mapbox': {
                                'style': "carto-positron",
                                'center': {'lat': -6.914744, 'lon': 107.609810},  # Bandung, Indonesia as default center
                                'zoom': 13
                            },
                            'margin': {'l': 0, 'r': 0, 't': 0, 'b': 0},
                            'height': 500,
                            'paper_bgcolor': 'rgba(0,0,0,0)',
                            'plot_bgcolor': 'rgba(0,0,0,0)',
                        }
                    },
                    config={
                        'displayModeBar': True,
                        'modeBarButtonsToRemove': ['select2d', 'lasso2d', 'resetScale2d'],
                        'displaylogo': False
                    },
                    className="map-container"
                )
            ], className="map-card"),
            
            # Current Location Info
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.Img(src="/static/icon/location.svg", className="param-icon"),
                            html.Div("Current Location", className="param-title")
                        ], className="d-flex align-items-center"),
                        html.Div(id="current-location-text", className="param-value", children="Not available")
                    ], className="col-md-6"),
                    
                    html.Div([
                        html.Div([
                            html.Img(src="/static/icon/compass.svg", className="param-icon"),
                            html.Div("Coordinates", className="param-title")
                        ], className="d-flex align-items-center"),
                        html.Div(id="current-coordinates", className="param-value", children="0.000, 0.000")
                    ], className="col-md-6"),
                ], className="row")
            ], className="param-card mt-3"),
        ], className="mb-4"),
        
        # Button Section
        html.Div([
            # html.Button("SETTING", className="btn btn-secondary m-1"),
            dcc.Link("MCS", href="/dash/engineer/", className="btn btn-secondary m-1"),
            dcc.Link("T&H INDOOR", href="/dash/engineer/th-in", className="btn btn-secondary m-1"),
            dcc.Link("PAR", href="/dash/engineer/par", className="btn btn-secondary m-1"),
            dcc.Link("CO2", href="/dash/engineer/co2", className="btn btn-secondary m-1"),
            dcc.Link("T&H OUTDOOR", href="/dash/engineer/th-out", className="btn btn-secondary m-1"),
            dcc.Link("WINDSPEED", href="/dash/engineer/windspeed", className="btn btn-secondary m-1"),
            dcc.Link("RAINFALL", href="/dash/engineer/rainfall", className="btn btn-secondary m-1"),
            dcc.Link("EPS", href="/dash/engineer/eps", className="btn btn-secondary m-1"),
            html.Button("LOGOUT", id="logout-button", className="btn btn-dark m-1"),
            dcc.Location(id="logout-redirect", refresh=True)  # Handles redirection
        ], className="d-flex flex-wrap justify-content-end mb-4")
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

    dcc.Interval(id='interval_gps', interval=1200, n_intervals=0)
])
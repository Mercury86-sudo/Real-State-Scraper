import dash
from dash import dcc, html, dash_table, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd
import os


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
app.title = "MERIDA.MARKET.WATCH"


app.index_string = '''
<!DOCTYPE html>
<html>
    <head>{%metas%}<title>{%title%}</title>{%favicon%}{%css%}
    <style>
        body { background-color: #000000 !important; font-family: 'Roboto Mono', monospace; }
        .card { background-color: #111111 !important; border: 1px solid #333 !important; border-radius: 0px !important; }
        .form-control, .Select-control { background-color: #000 !important; border: 1px solid #444 !important; color: #fff !important; }
        h1, h2, h3, h4, h5 { font-family: 'Helvetica Neue', sans-serif; font-weight: 300; letter-spacing: 1px; color: #fff; }
        ::-webkit-scrollbar { width: 8px; background: #000; }
        ::-webkit-scrollbar-thumb { background: #333; }
    </style>
    </head>
    <body>{%app_entry%}<footer>{%config%}{%scripts%}{%renderer%}</footer></body>
</html>
'''

def load_data():
    if os.path.exists("data.csv"):
        try:
            df = pd.read_csv("data.csv")
            df = df.dropna(subset=['Precio', 'Metros'])
            df = df[df['Precio_m2'] < 80000]
            return df
        except: return pd.DataFrame()
    return pd.DataFrame()

df_initial = load_data()
last_update = "UNKNOWN"
if os.path.exists("data.csv"):
    
    import datetime
    ts = os.path.getmtime("data.csv")
    last_update = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d %H:%M:%S')

app.layout = dbc.Container([
    
    
    dbc.Row([
        dbc.Col([
            html.H5("INMO.INTELLIGENCE // WEEKLY REPORT", className="mb-0 text-white"),
            html.Small(f"LAST DATA UPDATE: {last_update}", className="text-muted")
        ], width=8, className="pt-4"),
        dbc.Col([
            html.Div("LIVE FEED", className="text-end text-success pt-4 blink_me", style={"font-family": "monospace"})
        ], width=4)
    ], className="mb-4 border-bottom border-dark pb-3"),

    
    dbc.Row([
        dbc.Col([
            html.Label("FILTER ZONE", className="text-muted small"),
            dcc.Dropdown(
                id='dropdown-zona',
                options=[{'label': z, 'value': z} for z in sorted(df_initial['Ubicacion'].unique())] if not df_initial.empty else [],
                placeholder="ALL SECTORS",
                multi=True,
                style={'background': '#000', 'color': '#fff', 'border': '1px solid #333'}
            ),
        ], width=12)
    ], className="mb-4"),

    
    dbc.Row(id="kpi-row", className="mb-4 g-2"),

    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody(dcc.Graph(id="mapa-principal", style={"height": "550px"}, config={'displayModeBar': False}), className="p-0")
            ])
        ], width=12)
    ], className="mb-4"),

    
    dbc.Row([
        dbc.Col([
            html.H6("ASSET LEDGER", className="text-muted mb-2"),
            dash_table.DataTable(
                id='tabla-datos',
                page_size=12,
                sort_action="native",
                style_table={'overflowX': 'auto', 'border': '1px solid #333'},
                style_header={'backgroundColor': '#111', 'color': '#888', 'borderBottom': '2px solid #333', 'textAlign': 'left'},
                style_data={'backgroundColor': '#000', 'color': '#ccc', 'borderBottom': '1px solid #222', 'fontFamily': 'monospace', 'textAlign': 'left'},
                style_data_conditional=[{'if': {'row_index': 'odd'}, 'backgroundColor': '#050505'}]
            )
        ])
    ]),
], fluid=True, style={"padding": "0px 30px"})

@app.callback(
    [Output("kpi-row", "children"), Output("mapa-principal", "figure"), Output("tabla-datos", "data"), Output("tabla-datos", "columns")],
    [Input("dropdown-zona", "value")]
)
def update_view(zonas):
    df = load_data()
    if df.empty: return [], {}, [], []
    
    dff = df.copy()
    if zonas: dff = dff[dff['Ubicacion'].isin(zonas)]

   
    def kpi(l, v):
        return dbc.Col(dbc.Card(dbc.CardBody([html.Small(l, className="text-muted small"), html.H3(v, className="text-white")])), width=3)
    
    kpis = [kpi("ASSETS", f"{len(dff)}"), kpi("AVG PRICE", f"${dff['Precio'].mean()/1000000:,.2f}M"),
            kpi("AVG SIZE", f"{dff['Metros'].mean():.0f} m²"), kpi("YIELD/m²", f"${dff['Precio_m2'].mean():,.0f}")]

    
    fig = px.scatter_mapbox(dff, lat="lat", lon="lon", hover_name="Titulo", color="Precio_m2",
                            color_continuous_scale=["#333", "#FFF"], size="Metros", size_max=12, zoom=11, mapbox_style="carto-darkmatter")
    fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, paper_bgcolor="#000", plot_bgcolor="#000", coloraxis_showscale=False)

    cols = [{"name": i, "id": i} for i in ["Titulo", "Ubicacion", "Precio", "Metros", "Precio_m2"]]
    return kpis, fig, dff.to_dict('records'), cols
    server = app.server

if __name__ == "__main__":
    import webbrowser
    from threading import Timer
    Timer(1, lambda: webbrowser.open("http://127.0.0.1:8050/")).start()
    app.run(debug=True)

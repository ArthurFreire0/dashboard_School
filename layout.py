from dash import html, dcc

def create_layout():
    return html.Div([
        html.H1(" Dashboard Escolar — Aprovados e Rankings", style={"textAlign": "center"}),
        html.Hr(),

    dcc.Upload(
        id="upload-csv",
        children=html.Div([
            html.H2("Envie seu arquivo CSV", style={"margin": "0", "padding": "0"}),
            html.P("Arraste o arquivo para esta área ou clique para selecionar",
                style={"fontSize": "18px", "margin": "5px 0 0"})
        ]),
        style={
            "width": "100%",
            "height": "160px",
            "borderWidth": "3px",
            "borderStyle": "dashed",
            "borderRadius": "12px",
            "textAlign": "center",
            "backgroundColor": "#f9f9f9",
            "cursor": "pointer",
            "padding": "40px 10px",    # <-- ajusta o texto sem empurrar para fora
            "marginBottom": "30px"
        },
        multiple=False
    ),



        html.Div(id="upload-status", style={"color": "green", "fontWeight": "bold"}),
        dcc.Store(id="store-data"),
        html.Hr(),

        html.Div(id="dashboard-area")
    ], style={"width": "95%", "margin": "auto"})

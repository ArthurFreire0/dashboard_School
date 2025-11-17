
import os
import base64
import traceback
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.express as px

from layout import create_layout
from processing import (
    try_read_csv_bytes,
    process_raw_df_to_standard,
    SUBJECT_KEYS,
    STANDARD_COLS
)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Dash(__name__)
app.title = "Dashboard Escolar"
app.layout = create_layout()



#  Upload CSV

@app.callback(
    Output("upload-status", "children"),
    Output("store-data", "data"),
    Input("upload-csv", "contents"),
    State("upload-csv", "filename")
)
def handle_upload(contents, filename):
    if not contents:
        return "Nenhum arquivo carregado.", []

    try:
        header, encoded = contents.split(",", 1)
        decoded = base64.b64decode(encoded)

        df_raw = try_read_csv_bytes(decoded)
        df_std = process_raw_df_to_standard(df_raw)

        return f"Arquivo '{filename}' processado com sucesso!", df_std.to_dict("records")

    except Exception as e:
        traceback.print_exc()
        return f"Erro ao processar arquivo: {e}", []



# Dashboard

@app.callback(
    Output("dashboard-area", "children"),
    Input("store-data", "data")
)
def render_dashboard(store_data):
    if not store_data:
        return html.H3("Nenhum dado carregado.")

    df = pd.DataFrame(store_data)

    for c in SUBJECT_KEYS + ["media_geral"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")

    #  Gráfico de Aprovados 
    fig_aprov = px.pie(df, names="status", title="Aprovados x Reprovados", hole=0.3)
    fig_aprov.update_traces(textinfo="percent+label")

    #  Ranking alunos 
    df_rank = df.dropna(subset=["media_geral"]).copy()
    df_rank["media_geral"] = df_rank["media_geral"].round(1)

    top5 = df_rank.sort_values("media_geral", ascending=False).head(5)

    ranking_alunos = dash_table.DataTable(
    columns=[
        {"name": "Nome", "id": "nome"},
        {"name": "Turma", "id": "turma"},
        {"name": "Série", "id": "serie"},
        {"name": "Média", "id": "media_geral"},
    ],
    data = top5.to_dict("records"),

    style_table={
        "width": "80%",
        "margin": "0 auto",
        "maxWidth": "600px",
        "border": "1px solid #ccc",
    },

    style_cell={
        "textAlign": "center",     # 🔥 CENTRALIZA TUDO
        "padding": "6px",
        "fontSize": "14px",
    },

    style_header={
        "fontWeight": "bold",
        "backgroundColor": "#e0e0e0",
        "fontSize": "15px",
        "textAlign": "center",     # 🔥 CENTRALIZA CABEÇALHO
    },

    style_data={
        "height": "28px",
    }
    )


    # Ranking das séries
    df_series = df_rank.copy()

    df_series = (
        df_series.groupby("serie")["media_geral"]
        .mean()
        .round(1)
        .reset_index()
        .sort_values("media_geral", ascending=False)
    )

    ranking_series = dash_table.DataTable(
        columns=[
            {"name": "Série", "id": "serie"},
            {"name": "Média", "id": "media_geral"},
        ],
        data=df_series.to_dict("records"),   
        style_table={
            "width": "80%",               
            "margin": "0 auto",           
            "maxWidth": "350px",
            "border": "1px solid #ccc",
        },
        style_cell={
            "padding": "4px",
            "fontSize": "13px",
            "textAlign": "center",
        },
        style_header={
            "fontWeight": "bold",
            "backgroundColor": "#e0e0e0",
            "fontSize": "14px",
        },
        style_data={
            "height": "25px",
        }
    )



    # Tabela completa 
    for col in STANDARD_COLS:
        if col not in df.columns:
            df[col] = np.nan

    table = dash_table.DataTable(
        columns=[{"name": col.capitalize(), "id": col} for col in STANDARD_COLS],
        data=df.to_dict("records"),
        page_size=20,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto"},
        style_data_conditional=[
            {
                "if": {"filter_query": "{status} = 'Reprovado'"},
                "backgroundColor": "#ff7777",
                "color": "black",
                "fontWeight": "bold",
            }
        ]
    )

    # LAYOUT FINAL
    return html.Div([
        html.Div([
            html.Div([html.H3(" Aprovados x Reprovados"), dcc.Graph(figure=fig_aprov)],
                     style={"width":"49%","display":"inline-block"}),

            html.Div([
                html.H3(" Top 5 Alunos"),
                ranking_alunos,
                html.H3(" Melhores Séries"),
                ranking_series
            ], style={"width":"49%","display":"inline-block","marginLeft":"2%"})
        ]),

        html.Hr(),
        html.H3(" Tabela Geral"),
        table
    ])


if __name__ == "__main__":
    print(" ta rodando em http://127.0.0.1:8050")
    app.run(debug=True)

import os
import base64
import traceback
import pandas as pd
import numpy as np
from dash import Dash, html, dcc, dash_table, Input, Output, State
import plotly.graph_objects as go

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

    status_counts = df['status'].value_counts()
    labels = status_counts.index.tolist()
    values = status_counts.values.tolist()

    colors = ['#10b981' if label == 'Aprovado' else '#ef4444' for label in labels]

    fig_aprov = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.4,
        marker=dict(
            colors=colors,
            line=dict(color='#ffffff', width=2)
        ),
        textinfo='percent+label',
        textfont=dict(size=14),
        hoverinfo='label+percent+value',
        pull=[0.05] * len(labels)
    )])

    fig_aprov.update_layout(
        title="Aprovados x Reprovados",
        title_font_size=20,
        title_font_family="'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        title_font_color="#1e293b",
        font_family="'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(t=60, b=20, l=20, r=20)
    )

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
        "width": "100%",
        "margin": "0 auto",
        "border": "none",
        "borderRadius": "12px",
        "overflow": "hidden",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"
    },

    style_cell={
        "textAlign": "center",
        "padding": "12px",
        "fontSize": "14px",
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        "border": "none",
    },

    style_header={
        "fontWeight": "700",
        "backgroundColor": "#3b82f6",
        "color": "white",
        "fontSize": "15px",
        "textAlign": "center",
        "border": "none",
        "padding": "14px"
    },

    style_data={
        "backgroundColor": "#ffffff",
        "color": "#1e293b",
        "border": "none",
    },

    style_data_conditional=[
        {
            'if': {'row_index': 'odd'},
            'backgroundColor': '#f1f5f9'
        }
    ]
    )


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
            "width": "100%",
            "margin": "0 auto",
            "border": "none",
            "borderRadius": "12px",
            "overflow": "hidden",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)"
        },
        style_cell={
            "padding": "12px",
            "fontSize": "14px",
            "textAlign": "center",
            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            "border": "none",
        },
        style_header={
            "fontWeight": "700",
            "backgroundColor": "#8b5cf6",
            "color": "white",
            "fontSize": "15px",
            "border": "none",
            "padding": "14px"
        },
        style_data={
            "backgroundColor": "#ffffff",
            "color": "#1e293b",
            "border": "none",
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#faf5ff'
            }
        ]
    )


    for col in STANDARD_COLS:
        if col not in df.columns:
            df[col] = np.nan

    table = dash_table.DataTable(
        columns=[{"name": col.capitalize(), "id": col} for col in STANDARD_COLS],
        data=df.to_dict("records"),
        page_size=20,
        sort_action="native",
        filter_action="native",
        style_table={
            "overflowX": "auto",
            "borderRadius": "12px",
            "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            "width": "100%"
        },
        style_cell={
            "textAlign": "center",
            "padding": "12px",
            "fontSize": "14px",
            "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
            "border": "1px solid #e2e8f0",
            "minWidth": "100px",
            "maxWidth": "180px",
            "whiteSpace": "normal",
            "height": "auto"
        },
        style_header={
            "backgroundColor": "#1e293b",
            "color": "white",
            "fontWeight": "700",
            "fontSize": "15px",
            "padding": "14px",
            "border": "none",
            "whiteSpace": "normal",
            "height": "auto"
        },
        style_data={
            "backgroundColor": "#ffffff",
            "color": "#1e293b",
            "whiteSpace": "normal",
            "height": "auto"
        },
        style_data_conditional=[
            {
                "if": {"filter_query": "{status} = 'Reprovado'"},
                "backgroundColor": "#fee2e2",
                "color": "#991b1b",
                "fontWeight": "600",
            },
            {
                "if": {"filter_query": "{status} = 'Aprovado'"},
                "backgroundColor": "#dcfce7",
                "color": "#166534",
                "fontWeight": "600",
            },
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8fafc'
            }
        ]
    )

    return html.Div([
        html.Div([
            html.Div([
                html.Div([
                    html.H3("📊 Aprovados x Reprovados",
                           style={
                               "margin": "0 0 20px 0",
                               "color": "#1e293b",
                               "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                               "fontSize": "20px",
                               "fontWeight": "600"
                           }),
                    dcc.Graph(
                        figure=fig_aprov,
                        config={
                            'displayModeBar': False
                        }
                    )
                ], style={
                    "backgroundColor": "#ffffff",
                    "padding": "25px",
                    "borderRadius": "16px",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                    "border": "1px solid #e2e8f0"
                })
            ], style={"width": "48%", "display": "inline-block", "verticalAlign": "top"}),

            html.Div([
                # Top 5 Students Card
                html.Div([
                    html.H3("🏆 Top 5 Alunos",
                           style={
                               "margin": "0 0 15px 0",
                               "color": "#1e293b",
                               "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                               "fontSize": "20px",
                               "fontWeight": "600"
                           }),
                    ranking_alunos
                ], style={
                    "backgroundColor": "#ffffff",
                    "padding": "25px",
                    "borderRadius": "16px",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                    "marginBottom": "25px",
                    "border": "1px solid #e2e8f0"
                }),

                html.Div([
                    html.H3("🎓 Melhores Séries",
                           style={
                               "margin": "0 0 15px 0",
                               "color": "#1e293b",
                               "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                               "fontSize": "20px",
                               "fontWeight": "600"
                           }),
                    ranking_series
                ], style={
                    "backgroundColor": "#ffffff",
                    "padding": "25px",
                    "borderRadius": "16px",
                    "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                    "border": "1px solid #e2e8f0"
                })
            ], style={"width": "48%", "display": "inline-block", "marginLeft": "4%", "verticalAlign": "top"})
        ], style={"marginBottom": "40px"}),

        html.Div([
            html.H3("📋 Tabela Geral",
                   style={
                       "margin": "0 0 20px 0",
                       "color": "#1e293b",
                       "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                       "fontSize": "24px",
                       "fontWeight": "600"
                   }),
            table
        ], style={
            "backgroundColor": "#ffffff",
            "padding": "30px",
            "borderRadius": "16px",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
            "border": "1px solid #e2e8f0",
            "marginBottom": "40px",
            "width": "100%",
            "overflowX": "auto"
        })
    ], style={"maxWidth": "1600px", "margin": "0 auto", "width": "98%"})


if __name__ == "__main__":
    print(" ta rodando em http://127.0.0.1:8050")
    app.run(debug=True)

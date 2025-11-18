import pandas as pd
import numpy as np
from dash import html, dcc, dash_table
import plotly.graph_objects as go

from src.dashboard_school.processing import SUBJECT_KEYS, STANDARD_COLS

FONT_FAMILY = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"


class DashboardBuilder:
    def prepare_dataframe(self, store_data):
        """
        Create base df and df_rank (only rows with media_geral), converting numeric columns and rounding.
        """
        df = pd.DataFrame(store_data)

        for c in SUBJECT_KEYS + ["media_geral"]:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce")
            else:
                df[c] = np.nan

        df_rank = df.dropna(subset=["media_geral"]).copy()
        if "media_geral" in df_rank:
            df_rank["media_geral"] = df_rank["media_geral"].round(1)

        return df, df_rank

    def build_status_pie(self, df):
        """
        Build the Aprovados x Reprovados pie figure.
        """
        status_counts = df.get("status", pd.Series(dtype=object)).value_counts()
        labels = status_counts.index.tolist()
        values = status_counts.values.tolist()

        colors = ["#10b981" if label == "Aprovado" else "#ef4444" for label in labels]

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.4,
                    marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
                    textinfo="percent+label",
                    textfont=dict(size=14),
                    hoverinfo="label+percent+value",
                    pull=[0.05] * len(labels),
                )
            ]
        )

        fig.update_layout(
            title="Aprovados x Reprovados",
            title_font_size=20,
            title_font_family=FONT_FAMILY,
            title_font_color="#1e293b",
            font_family=FONT_FAMILY,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(t=60, b=20, l=20, r=20),
        )
        return fig


    def build_top_students_table(self, df_rank):
        """
        Build the Top 5 students DataTable.
        """
        cols = [
            {"name": "Nome", "id": "nome"},
            {"name": "Turma", "id": "turma"},
            {"name": "Série", "id": "serie"},
            {"name": "Média", "id": "media_geral"},
        ]

        top5 = (
            df_rank.sort_values("media_geral", ascending=False)
            .head(5)
            .to_dict("records")
        )

        return dash_table.DataTable(
            columns=cols,
            data=top5,
            style_table={
                "width": "100%",
                "margin": "0 auto",
                "border": "none",
                "borderRadius": "12px",
                "overflow": "hidden",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            },
            style_cell={
                "textAlign": "center",
                "padding": "12px",
                "fontSize": "14px",
                "fontFamily": FONT_FAMILY,
                "border": "none",
            },
            style_header={
                "fontWeight": "700",
                "backgroundColor": "#3b82f6",
                "color": "white",
                "fontSize": "15px",
                "textAlign": "center",
                "border": "none",
                "padding": "14px",
            },
            style_data={"backgroundColor": "#ffffff", "color": "#1e293b", "border": "none"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#f1f5f9"}
            ],
        )


    def build_series_ranking_table(self, df_rank):
        """
        Build the ranking by series DataTable.
        """
        df_series = (
            df_rank.groupby("serie")["media_geral"].mean().round(1).reset_index()
            if not df_rank.empty and "serie" in df_rank.columns
            else pd.DataFrame(columns=["serie", "media_geral"])
        )
        df_series = df_series.sort_values("media_geral", ascending=False)

        return dash_table.DataTable(
            columns=[{"name": "Série", "id": "serie"}, {"name": "Média", "id": "media_geral"}],
            data=df_series.to_dict("records"),
            style_table={
                "width": "100%",
                "margin": "0 auto",
                "border": "none",
                "borderRadius": "12px",
                "overflow": "hidden",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
            },
            style_cell={
                "padding": "12px",
                "fontSize": "14px",
                "textAlign": "center",
                "fontFamily": FONT_FAMILY,
                "border": "none",
            },
            style_header={
                "fontWeight": "700",
                "backgroundColor": "#8b5cf6",
                "color": "white",
                "fontSize": "15px",
                "border": "none",
                "padding": "14px",
            },
            style_data={"backgroundColor": "#ffffff", "color": "#1e293b", "border": "none"},
            style_data_conditional=[
                {"if": {"row_index": "odd"}, "backgroundColor": "#faf5ff"}
            ],
        )


    def ensure_standard_columns(self, df):
        """
        Ensure all STANDARD_COLS exist in df.
        """
        for col in STANDARD_COLS:
            if col not in df.columns:
                df[col] = np.nan
        return df


    def build_main_table(self, df):
        """
        Build the general DataTable with filtering, sorting and conditional styling.
        """
        return dash_table.DataTable(
            columns=[{"name": col.capitalize(), "id": col} for col in STANDARD_COLS],
            data=df.to_dict("records"),
            page_size=20,
            sort_action="native",
            filter_action="native",
            style_table={
                "overflowX": "auto",
                "borderRadius": "12px",
                "boxShadow": "0 2px 8px rgba(0,0,0,0.08)",
                "width": "100%",
            },
            style_cell={
                "textAlign": "center",
                "padding": "12px",
                "fontSize": "14px",
                "fontFamily": FONT_FAMILY,
                "border": "1px solid #e2e8f0",
                "minWidth": "100px",
                "maxWidth": "180px",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_header={
                "backgroundColor": "#1e293b",
                "color": "white",
                "fontWeight": "700",
                "fontSize": "15px",
                "padding": "14px",
                "border": "none",
                "whiteSpace": "normal",
                "height": "auto",
            },
            style_data={
                "backgroundColor": "#ffffff",
                "color": "#1e293b",
                "whiteSpace": "normal",
                "height": "auto",
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
                {"if": {"row_index": "odd"}, "backgroundColor": "#f8fafc"},
            ],
        )


    def render_dashboard(self, store_data):
        if not store_data:
            return html.H3("Nenhum dado carregado.")

        df, df_rank = self.prepare_dataframe(store_data)
        df = self.ensure_standard_columns(df)

        fig_aprov = self.build_status_pie(df)
        ranking_alunos = self.build_top_students_table(df_rank)
        ranking_series = self.build_series_ranking_table(df_rank)
        table = self.build_main_table(df)

        return html.Div(
            [
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "📊 Aprovados x Reprovados",
                                            style={
                                                "margin": "0 0 20px 0",
                                                "color": "#1e293b",
                                                "fontFamily": FONT_FAMILY,
                                                "fontSize": "20px",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        dcc.Graph(figure=fig_aprov, config={"displayModeBar": False}),
                                    ],
                                    style={
                                        "backgroundColor": "#ffffff",
                                        "padding": "25px",
                                        "borderRadius": "16px",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                                        "border": "1px solid #e2e8f0",
                                    },
                                )
                            ],
                            style={"width": "48%", "display": "inline-block", "verticalAlign": "top"},
                        ),
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.H3(
                                            "🏆 Top 5 Alunos",
                                            style={
                                                "margin": "0 0 15px 0",
                                                "color": "#1e293b",
                                                "fontFamily": FONT_FAMILY,
                                                "fontSize": "20px",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        ranking_alunos,
                                    ],
                                    style={
                                        "backgroundColor": "#ffffff",
                                        "padding": "25px",
                                        "borderRadius": "16px",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                                        "marginBottom": "25px",
                                        "border": "1px solid #e2e8f0",
                                    },
                                ),
                                html.Div(
                                    [
                                        html.H3(
                                            "🎓 Melhores Séries",
                                            style={
                                                "margin": "0 0 15px 0",
                                                "color": "#1e293b",
                                                "fontFamily": FONT_FAMILY,
                                                "fontSize": "20px",
                                                "fontWeight": "600",
                                            },
                                        ),
                                        ranking_series,
                                    ],
                                    style={
                                        "backgroundColor": "#ffffff",
                                        "padding": "25px",
                                        "borderRadius": "16px",
                                        "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                                        "border": "1px solid #e2e8f0",
                                    },
                                ),
                            ],
                            style={
                                "width": "48%",
                                "display": "inline-block",
                                "marginLeft": "4%",
                                "verticalAlign": "top",
                            },
                        ),
                    ],
                    style={"marginBottom": "40px"},
                ),
                html.Div(
                    [
                        html.H3(
                            "📋 Tabela Geral",
                            style={
                                "margin": "0 0 20px 0",
                                "color": "#1e293b",
                                "fontFamily": FONT_FAMILY,
                                "fontSize": "24px",
                                "fontWeight": "600",
                            },
                        ),
                        table,
                    ],
                    style={
                        "backgroundColor": "#ffffff",
                        "padding": "30px",
                        "borderRadius": "16px",
                        "boxShadow": "0 4px 6px rgba(0,0,0,0.07)",
                        "border": "1px solid #e2e8f0",
                        "marginBottom": "40px",
                        "width": "100%",
                        "overflowX": "auto",
                    },
                ),
            ],
            style={"maxWidth": "1600px", "margin": "0 auto", "width": "98%"},
        )
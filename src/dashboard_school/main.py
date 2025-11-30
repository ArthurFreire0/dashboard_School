import logging
import sys
import os
import base64
import io
import traceback
import pandas as pd

from dash import Dash, Input, Output, State, html, dcc
from dashboard_school.components.dashboard import DashboardBuilder
from dashboard_school.components.layout import create_layout
from dashboard_school.processing import try_read_csv_bytes, process_university_data


# Inicialização do app
app = Dash(__name__)
logger = logging.getLogger(__name__)

app.title = "Sistema de Análise Acadêmica Universitária"
dashboard = DashboardBuilder()
app.layout = create_layout()


@app.callback(
    [Output("upload-status", "children"),
     Output("store-data", "data")],
    [Input("upload-csv", "contents")],
    [State("upload-csv", "filename")]
)
def handle_upload(contents, filename):
    """Recebe o CSV enviado pelo usuário."""
    if not contents:
        return "", []

    try:
        # Decodificar o arquivo em Base64
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Ler CSV
        try:
            df_raw = try_read_csv_bytes(decoded)
        except Exception as e:
            error_msg = html.Div([
                html.H3("❌ Erro ao Ler o Arquivo CSV", style={'color': '#dc2626'}),
                html.P(f"Detalhes técnicos: {str(e)}")
            ])
            return error_msg, []

        # Processar dados
        try:
            df_processed = process_university_data(df_raw)
        except Exception as e:
            error_msg = html.Div([
                html.H3("❌ Erro ao Processar os Dados", style={'color': '#dc2626'}),
                html.P(f"Detalhes técnicos: {str(e)}")
            ])
            return error_msg, []

        if len(df_processed) == 0:
            return html.Div("⚠️ Arquivo sem dados válidos."), []

        # Converter para JSON
        data_json = df_processed.to_json(date_format='iso', orient='split')

        # Mensagem de sucesso
        success_msg = html.Div([
            html.H3("✅ Arquivo Carregado com Sucesso!", style={'color': '#10b981'}),
            html.P([
                f"📄 Arquivo: {filename}",
                html.Br(),
                f"📊 Total de registros: {len(df_processed)}",
                html.Br(),
                f"👥 Total de alunos: {df_processed['student_id'].nunique()}",
                html.Br(),
                f"📚 Total de disciplinas: {df_processed['discipline'].nunique()}"
            ])
        ])

        return success_msg, data_json

    except Exception as e:
        traceback.print_exc()
        return html.Div(f"❌ Erro inesperado: {str(e)}"), []


@app.callback(
    Output("dashboard-area", "children"),
    [Input("store-data", "data")]
)
def update_dashboard(data_json):
    """Atualiza o dashboard baseado nos dados processados."""
    if not data_json:
        return html.Div()

    try:
        df = pd.read_json(io.StringIO(data_json), orient='split')

        stats_cards = dashboard.build_statistics_cards(df)
        admission_pie = dashboard.build_admission_type_pie(df)
        failure_bar = dashboard.build_failure_rate_by_discipline_bar(df)
        attendance_scatter = dashboard.build_approval_vs_attendance_scatter(df)
        churn_gauge = dashboard.build_churn_risk_gauge(df)
        course_eval_gauge = dashboard.build_course_evaluation_gauge(df)
        churn_table = dashboard.build_churn_risk_table(df)
        main_table = dashboard.build_main_data_table(df)

        return html.Div([
            stats_cards,

            # Gráficos principais
            html.Div([
                html.Div([
                    html.H2("📊 Distribuição de Formas de Ingresso"),
                    dcc.Graph(figure=admission_pie, config={'displayModeBar': False},style={'height':'350px'})
                ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),

                html.Div([
                    html.H2("⚠️ Risco de Evasão"),
                    dcc.Graph(figure=churn_gauge, config={'displayModeBar': False},style={'height':'350px'})
                ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),

                html.Div([
                    html.H2("⭐ Avaliação do Curso"),
                    dcc.Graph(figure=course_eval_gauge, config={'displayModeBar': False},style={'height':'350px'})
                ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px', 'flex': '1'}),
            ], style={'display': 'flex', 'gap': '20px', 'flexWrap': 'wrap'}),

            html.Div([
                html.H2("🎯 Reprovação por Disciplina"),
                dcc.Graph(figure=failure_bar, config={'displayModeBar': False})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px'}),

            html.Div([
                html.H2("📈 Frequência vs Nota Final"),
                dcc.Graph(figure=attendance_scatter, config={'displayModeBar': False})
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px'}),

            html.Div([
                html.H2("🚨 Alunos com Maior Risco de Evasão"),
                churn_table
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px'}),

            html.Div([
                html.H2("📋 Dados Completos"),
                main_table
            ], style={'backgroundColor': 'white', 'padding': '20px', 'borderRadius': '12px'})
        ])

    except Exception as e:
        traceback.print_exc()
        return html.Div(f"❌ Erro ao gerar dashboard: {str(e)}")


if __name__ == "__main__":
    print("🎓 Dashboard de Análise Acadêmica Universitária")
    print("="*60)
    print("\n🌐 Acesse o dashboard em: http://localhost:3000")
    print("⚠️  Pressione Ctrl+C para parar o servidor\n")
    app.run(debug=True, port=3000)

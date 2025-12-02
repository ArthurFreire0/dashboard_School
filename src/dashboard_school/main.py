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
from dashboard_school.modules.connection import init_db, SessionLocal
from dashboard_school.modules.models import Discipline, Student, AdmissionTypeEnum, EnrollmentStatusEnum, \
    PaymentStatusEnum, DisciplineStatusEnum, Grade
from src.dashboard_school.processing import try_read_csv_bytes, process_university_data


init_db()

app = Dash(__name__)
logger = logging.getLogger(__name__)

app.title = "Sistema de Análise Acadêmica Universitária"
dashboard = DashboardBuilder()
app.layout = create_layout()


def save_data_to_database(df):
    """Save processed data to modules."""
    session = SessionLocal()
    disciplines_dict = {}

    for discipline_name in df['discipline'].unique():
        if discipline_name and str(discipline_name) != 'nan':
            discipline = session.query(Discipline).filter_by(name=discipline_name).first()
            if not discipline:
                discipline = Discipline(name=discipline_name)
                session.add(discipline)
                session.flush()
            disciplines_dict[discipline_name] = discipline.id

    students_dict = {}
    unique_students = df.drop_duplicates(subset=['student_id'])

    for idx, row in unique_students.iterrows():
        student_id = str(row['student_id'])
        if student_id and student_id != 'nan':
            student = session.query(Student).filter_by(student_id=student_id).first()
            if not student:
                admission_map = {
                    'transferencia_externa': AdmissionTypeEnum.EXTERNAL_TRANSFER,
                    'transferencia_interna': AdmissionTypeEnum.INTERNAL_TRANSFER,
                    'bolsista': AdmissionTypeEnum.SCHOLARSHIP,
                    'vestibular': AdmissionTypeEnum.ENTRANCE_EXAM,
                    'promocao': AdmissionTypeEnum.SCHOLARSHIP
                }
                admission_type = admission_map.get(
                    row.get('admission_type', 'vestibular'),
                    AdmissionTypeEnum.ENTRANCE_EXAM
                )

                enrollment_map = {
                    'ativo': EnrollmentStatusEnum.ACTIVE,
                    'evadido': EnrollmentStatusEnum.DROPPED,
                    'trancado': EnrollmentStatusEnum.SUSPENDED
                }
                enrollment_status = enrollment_map.get(
                    row.get('enrollment_status', 'ativo'),
                    EnrollmentStatusEnum.ACTIVE
                )

                student = Student(
                    student_id=student_id,
                    course=str(row.get('course', '')),
                    admission_type=admission_type,
                    enrollment_status=enrollment_status
                )
                session.add(student)
                session.flush()
            students_dict[student_id] = student.id

    for _, row in df.iterrows():
        student_id_str = str(row['student_id'])
        discipline_name = row['discipline']

        if (student_id_str in students_dict and
            discipline_name and str(discipline_name) != 'nan' and
            discipline_name in disciplines_dict):

            payment_map = {
                'pago': PaymentStatusEnum.PAID,
                'pendente': PaymentStatusEnum.PENDING,
                'atrasado': PaymentStatusEnum.OVERDUE
            }
            payment_status = payment_map.get(
                row.get('payment_status', 'pendente'),
                PaymentStatusEnum.PENDING
            )

            discipline_status_map = {
                'aprovado': DisciplineStatusEnum.APPROVED,
                'reprovado': DisciplineStatusEnum.FAILED,
                'em_andamento': DisciplineStatusEnum.IN_PROGRESS
            }
            discipline_status = discipline_status_map.get(
                row.get('discipline_status', 'em_andamento'),
                DisciplineStatusEnum.IN_PROGRESS
            )

            grade = Grade(
                student_id=students_dict[student_id_str],
                discipline_id=disciplines_dict[discipline_name],
                semester=str(row.get('semester', '')),
                final_grade=float(row['final_grade']) if pd.notna(row.get('final_grade')) else None,
                attendance_pct=float(row['attendance_pct']) if pd.notna(row.get('attendance_pct')) else None,
                payment_status=payment_status,
                discipline_status=discipline_status,
                course_evaluation=int(row['course_evaluation']) if pd.notna(row.get('course_evaluation')) else None
            )
            session.add(grade)

    session.commit()

@app.callback(
    [Output("upload-status", "children"),
     Output("store-data", "data")],
    [Input("upload-csv", "contents")],
    [State("upload-csv", "filename")]
)
def handle_upload(contents, filename):
    """Handle CSV file upload."""
    if not contents:
        return "", []

    try:
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        try:
            df_raw = try_read_csv_bytes(decoded)
        except Exception as e:
            error_msg = html.Div([
                html.H3("❌ Erro ao Ler o Arquivo CSV", style={'color': '#dc2626', 'marginBottom': '10px'}),
                html.P([
                    "Não foi possível ler o arquivo. Verifique se:",
                    html.Ul([
                        html.Li("O arquivo está no formato CSV correto"),
                        html.Li("O arquivo não está corrompido"),
                        html.Li("O encoding está correto (UTF-8, Latin1, etc.)"),
                    ], style={'marginTop': '10px', 'marginBottom': '10px'}),
                    html.P(f"Detalhes técnicos: {str(e)}", style={'fontSize': '12px', 'color': '#64748b', 'fontStyle': 'italic'})
                ], style={'color': '#1e293b'})
            ], style={'padding': '15px', 'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'border': '2px solid #dc2626'})
            return error_msg, []

        required_cols = ['id_aluno', 'curso', 'periodo_letivo', 'disciplina', 'nota_final',
                        'frequencia_pct', 'status_pagamento', 'status_disciplina',
                        'nota_avaliacao_curso', 'status_matricula']

        df_cols_normalized = [str(col).lower().strip() for col in df_raw.columns]
        missing_cols = []

        for req_col in required_cols:
            req_normalized = req_col.lower().replace('_', ' ').strip()
            found = False
            for df_col in df_cols_normalized:
                df_col_clean = df_col.replace('_', ' ').strip()
                if req_normalized in df_col_clean or df_col_clean in req_normalized:
                    found = True
                    break
            if not found:
                missing_cols.append(req_col)

        if missing_cols and len(missing_cols) > 5:
            error_msg = html.Div([
                html.H3("❌ Formato de CSV Inválido", style={'color': '#dc2626', 'marginBottom': '10px'}),
                html.P([
                    "O arquivo CSV não possui as colunas necessárias.",
                    html.Br(),
                    html.Br(),
                    html.Strong("Colunas esperadas:"),
                    html.Ul([
                        html.Li("id_aluno - Identificador do aluno"),
                        html.Li("curso - Nome do curso"),
                        html.Li("periodo_letivo - Período/semestre (ex: 2024.1)"),
                        html.Li("disciplina - Nome da disciplina"),
                        html.Li("nota_final - Nota final (0-10)"),
                        html.Li("frequencia_pct - Frequência em % (0-100)"),
                        html.Li("status_pagamento - pago, pendente ou atrasado"),
                        html.Li("status_disciplina - aprovado, reprovado ou em_andamento"),
                        html.Li("nota_avaliacao_curso - Avaliação do curso (1-10)"),
                        html.Li("status_matricula - ativo, evadido ou trancado"),
                        html.Li("forma_ingresso - vestibular, transferencia_externa, etc. (opcional)"),
                    ], style={'marginTop': '10px', 'marginBottom': '10px'}),
                    html.Strong(f"Colunas encontradas no arquivo: ", style={'color': '#dc2626'}),
                    html.P(", ".join(df_raw.columns[:10]) + ("..." if len(df_raw.columns) > 10 else ""),
                          style={'fontSize': '13px', 'color': '#64748b', 'marginTop': '5px'})
                ], style={'color': '#1e293b', 'fontSize': '14px'})
            ], style={'padding': '20px', 'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'border': '2px solid #dc2626'})
            return error_msg, []

        try:
            df_processed = process_university_data(df_raw)
        except Exception as e:
            error_msg = html.Div([
                html.H3("❌ Erro ao Processar os Dados", style={'color': '#dc2626', 'marginBottom': '10px'}),
                html.P([
                    "Os dados foram lidos, mas há problemas no conteúdo:",
                    html.Ul([
                        html.Li("Verifique se os valores numéricos estão corretos (nota_final, frequencia_pct)"),
                        html.Li("Verifique se os status estão escritos corretamente"),
                        html.Li("Certifique-se de que não há valores inválidos nas colunas"),
                    ], style={'marginTop': '10px', 'marginBottom': '10px'}),
                    html.P(f"Detalhes técnicos: {str(e)}", style={'fontSize': '12px', 'color': '#64748b', 'fontStyle': 'italic'})
                ], style={'color': '#1e293b'})
            ], style={'padding': '15px', 'backgroundColor': '#fef3c7', 'borderRadius': '8px', 'border': '2px solid #f59e0b'})
            return error_msg, []

        if len(df_processed) == 0:
            error_msg = html.Div([
                html.H3("⚠️ Arquivo Vazio", style={'color': '#f59e0b', 'marginBottom': '10px'}),
                html.P("O arquivo CSV não contém nenhum registro válido. Verifique se o arquivo possui dados.",
                      style={'color': '#1e293b'})
            ], style={'padding': '15px', 'backgroundColor': '#fef3c7', 'borderRadius': '8px', 'border': '2px solid #f59e0b'})
            return error_msg, []

        try:
            save_data_to_database(df_processed)
        except Exception as e:
            logger.warning(f"⚠️ Warning: Could not save to modules: {e}")

        data_json = df_processed.to_json(date_format='iso', orient='split')

        success_msg = html.Div([
            html.H3("✅ Arquivo Carregado com Sucesso!", style={'color': '#10b981', 'marginBottom': '10px'}),
            html.P([
                f"📄 Arquivo: {filename}",
                html.Br(),
                f"📊 Total de registros: {len(df_processed)}",
                html.Br(),
                f"👥 Total de alunos: {df_processed['student_id'].nunique()}",
                html.Br(),
                f"📚 Total de disciplinas: {df_processed['discipline'].nunique()}",
            ], style={'color': '#1e293b', 'fontSize': '14px', 'lineHeight': '1.8'})
        ], style={'padding': '15px', 'backgroundColor': '#d1fae5', 'borderRadius': '8px', 'border': '2px solid #10b981'})

        return success_msg, data_json

    except Exception as e:
        traceback.print_exc()
        error_msg = html.Div([
            html.H3("❌ Erro Inesperado", style={'color': '#dc2626', 'marginBottom': '10px'}),
            html.P([
                "Ocorreu um erro inesperado ao processar o arquivo.",
                html.Br(),
                html.Br(),
                "Por favor, verifique se o arquivo está no formato correto e tente novamente.",
                html.Br(),
                html.Br(),
                html.Details([
                    html.Summary("Ver detalhes técnicos do erro", style={'cursor': 'pointer', 'color': '#64748b'}),
                    html.P(str(e), style={'fontSize': '12px', 'color': '#64748b', 'fontFamily': 'monospace', 'marginTop': '10px'})
                ])
            ], style={'color': '#1e293b'})
        ], style={'padding': '15px', 'backgroundColor': '#fee2e2', 'borderRadius': '8px', 'border': '2px solid #dc2626'})
        return error_msg, []


@app.callback(
    Output("dashboard-area", "children"),
    [Input("store-data", "data")]
)
def update_dashboard(data_json):
    """Update dashboard with processed data."""
    if not data_json:
        return html.Div()

    try:
        df = pd.read_json(io.StringIO(data_json), orient='split')

        stats_cards = dashboard.build_statistics_cards(df)

        admission_pie = dashboard.build_admission_type_pie(df)
        failure_bar = dashboard.build_failure_rate_by_discipline_bar(df)
        churn_gauge = dashboard.build_churn_risk_gauge(df)
        course_eval_gauge = dashboard.build_course_evaluation_gauge(df)

        churn_table = dashboard.build_churn_risk_table(df)
        main_table = dashboard.build_main_data_table(df)

        return html.Div([
            stats_cards,

            html.Div([
                html.Div([
                    html.H2("📊 Distribuição de Formas de Ingresso",
                           style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                    dcc.Graph(figure=admission_pie, config={'displayModeBar': False, 'responsive': False}, style={'height': '400px'})
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'flex': '1',
                    'minWidth': '300px',
                    'overflow': 'hidden'
                }),

                html.Div([
                    html.H2("⚠️ Indicador de Risco de Evasão",
                           style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                    dcc.Graph(figure=churn_gauge, config={'displayModeBar': False, 'responsive': False}, style={'height': '350px'})
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'flex': '1',
                    'minWidth': '300px',
                    'overflow': 'hidden'
                }),

                html.Div([
                    html.H2("⭐ Avaliação do Curso pelos Alunos",
                           style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                    dcc.Graph(figure=course_eval_gauge, config={'displayModeBar': False, 'responsive': False}, style={'height': '350px'})
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'flex': '1',
                    'minWidth': '300px',
                    'overflow': 'hidden'
                })
            ], style={
                'display': 'flex',
                'justifyContent': 'space-between',
                'gap': '20px',
                'marginBottom': '30px',
                'flexWrap': 'wrap'
            }),

            html.Div([
                html.H2("🎯 Gargalos: Taxa de Reprovação por Disciplina",
                       style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                dcc.Graph(figure=failure_bar, config={'displayModeBar': False})
            ], style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'marginBottom': '30px'
            }),

            html.Div([
                html.H2("🚨 Alunos em Alto Risco de Evasão",
                       style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                churn_table
            ], style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'marginBottom': '30px'
            }),

            html.Div([
                html.H2("📋 Dados Completos",
                       style={'fontSize': '20px', 'marginBottom': '15px', 'color': '#1e293b'}),
                main_table
            ], style={
                'backgroundColor': '#ffffff',
                'padding': '20px',
                'borderRadius': '12px',
                'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                'marginBottom': '30px'
            })
        ])

    except Exception as e:
        traceback.print_exc()

        error_type = type(e).__name__
        error_message = str(e)

        if "numeric" in error_message.lower() and "dtype" in error_message.lower():
            return html.Div([
                html.Div([
                    html.H2("⚠️ Erro nos Dados Numéricos", style={'color': '#dc2626', 'marginBottom': '15px'}),
                    html.P([
                        "Os dados foram carregados, mas algumas colunas que deveriam conter números possuem valores inválidos.",
                        html.Br(),
                        html.Br(),
                        html.Strong("Colunas numéricas esperadas:"),
                        html.Ul([
                            html.Li([html.Strong("nota_final"), " - Deve conter apenas números de 0 a 10"]),
                            html.Li([html.Strong("frequencia_pct"), " - Deve conter apenas números de 0 a 100"]),
                            html.Li([html.Strong("nota_avaliacao_curso"), " - Deve conter apenas números de 1 a 10"]),
                        ], style={'marginTop': '10px'}),
                        html.Br(),
                        html.Strong("Verifique se:"),
                        html.Ul([
                            html.Li("As colunas numéricas não contêm texto"),
                            html.Li("Está usando ponto (.) ao invés de vírgula (,) para decimais"),
                            html.Li("Não há células vazias ou com caracteres especiais"),
                        ], style={'marginTop': '10px', 'marginBottom': '15px'}),
                        html.P([
                            html.Strong("Exemplo correto:"),
                            html.Br(),
                            "nota_final: 7.5 ✅",
                            html.Br(),
                            "nota_final: 7,5 ❌",
                            html.Br(),
                            "nota_final: sete ❌",
                        ], style={'backgroundColor': '#f1f5f9', 'padding': '10px', 'borderRadius': '5px', 'fontSize': '13px'}),
                    ], style={'fontSize': '14px', 'color': '#1e293b', 'lineHeight': '1.6'}),
                    html.Details([
                        html.Summary("🔧 Ver detalhes técnicos", style={'cursor': 'pointer', 'color': '#64748b', 'marginTop': '15px'}),
                        html.Pre(f"{error_type}: {error_message}",
                                style={'fontSize': '11px', 'color': '#64748b', 'backgroundColor': '#f8fafc',
                                       'padding': '10px', 'borderRadius': '5px', 'marginTop': '10px', 'overflow': 'auto'})
                    ])
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '30px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
                    'maxWidth': '800px',
                    'margin': '40px auto',
                    'border': '3px solid #fecaca'
                })
            ])

        elif "key" in error_message.lower() or "column" in error_message.lower():
            return html.Div([
                html.Div([
                    html.H2("⚠️ Erro na Estrutura dos Dados", style={'color': '#dc2626', 'marginBottom': '15px'}),
                    html.P([
                        "O arquivo foi processado, mas está faltando alguma coluna necessária para gerar os gráficos.",
                        html.Br(),
                        html.Br(),
                        "Isso pode acontecer se o arquivo CSV estiver incompleto ou com formato diferente do esperado.",
                        html.Br(),
                        html.Br(),
                        html.Strong("Solução:"),
                        html.Br(),
                        "Faça o upload novamente do arquivo CSV e certifique-se de que todas as colunas obrigatórias estão presentes.",
                    ], style={'fontSize': '14px', 'color': '#1e293b', 'lineHeight': '1.6'}),
                    html.Details([
                        html.Summary("🔧 Ver detalhes técnicos", style={'cursor': 'pointer', 'color': '#64748b', 'marginTop': '15px'}),
                        html.Pre(f"{error_type}: {error_message}",
                                style={'fontSize': '11px', 'color': '#64748b', 'backgroundColor': '#f8fafc',
                                       'padding': '10px', 'borderRadius': '5px', 'marginTop': '10px', 'overflow': 'auto'})
                    ])
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '30px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
                    'maxWidth': '800px',
                    'margin': '40px auto',
                    'border': '3px solid #fed7aa'
                })
            ])

        else:
            return html.Div([
                html.Div([
                    html.H2("❌ Erro ao Gerar Dashboard", style={'color': '#dc2626', 'marginBottom': '15px'}),
                    html.P([
                        "Ocorreu um erro inesperado ao processar os dados para exibição.",
                        html.Br(),
                        html.Br(),
                        html.Strong("Possíveis causas:"),
                        html.Ul([
                            html.Li("Dados no formato incorreto"),
                            html.Li("Valores inconsistentes nas colunas"),
                            html.Li("Arquivo CSV corrompido"),
                        ], style={'marginTop': '10px'}),
                        html.Br(),
                        html.Strong("O que fazer:"),
                        html.Br(),
                        "1. Verifique o arquivo CSV",
                        html.Br(),
                        "2. Tente fazer o upload novamente",
                    ], style={'fontSize': '14px', 'color': '#1e293b', 'lineHeight': '1.6'}),
                    html.Details([
                        html.Summary("🔧 Ver detalhes técnicos", style={'cursor': 'pointer', 'color': '#64748b', 'marginTop': '15px'}),
                        html.Pre(f"{error_type}: {error_message}",
                                style={'fontSize': '11px', 'color': '#64748b', 'backgroundColor': '#f8fafc',
                                       'padding': '10px', 'borderRadius': '5px', 'marginTop': '10px', 'overflow': 'auto'})
                    ])
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '30px',
                    'borderRadius': '12px',
                    'boxShadow': '0 4px 12px rgba(0,0,0,0.1)',
                    'maxWidth': '800px',
                    'margin': '40px auto',
                    'border': '3px solid #fecaca'
                })
            ])


if __name__ == "__main__":
    app.run(debug=True, port=3000)

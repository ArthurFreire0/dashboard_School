import pandas as pd
import plotly.graph_objects as go
from dash import html, dash_table

from src.dashboard_school.processing import calculate_churn_probability, get_churn_risk_level

FONT_FAMILY = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"

COLOR_PALETTE = {
    'primary': '#3b82f6',
    'success': '#10b981',
    'danger': '#ef4444',
    'warning': '#f59e0b',
    'info': '#06b6d4',
    'purple': '#8b5cf6',
    'pink': '#ec4899'
}


class DashboardBuilder:
    """Build comprehensive university analytics dashboard."""

    def prepare_dataframe(self, store_data):
        """Prepare and clean dataframe from store data."""
        if not store_data:
            return pd.DataFrame()

        df = pd.DataFrame(store_data)

        numeric_cols = ['final_grade', 'attendance_pct', 'course_evaluation']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')

        return df

    def build_admission_type_pie(self, df: pd.DataFrame):
        """Build pie chart showing distribution of admission types."""
        if df.empty or 'admission_type' not in df.columns:
            return go.Figure()

        df_students = df.drop_duplicates(subset=['student_id'])
        admission_counts = df_students['admission_type'].value_counts()

        label_map = {
            'transferencia_externa': 'Transferência Externa',
            'transferencia_interna': 'Transferência Interna',
            'bolsista': 'Bolsista/Promoção',
            'vestibular': 'Vestibular'
        }

        labels = [label_map.get(x, x) for x in admission_counts.index]
        values = admission_counts.values

        colors = ['#3b82f6', '#10b981', '#f59e0b', '#8b5cf6']

        fig = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=colors, line=dict(color='#ffffff', width=2)),
            textinfo='percent+label',
            textfont=dict(size=13),
            hovertemplate='<b>%{label}</b><br>Alunos: %{value}<br>Percentual: %{percent}<extra></extra>'
        )])

        fig.update_layout(
            title_font_size=18,
            title_font_family=FONT_FAMILY,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=20, b=20, l=20, r=20),
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
            height=400
        )

        return fig

    def build_failure_rate_by_discipline_bar(self, df: pd.DataFrame):
        """Build bar chart showing failure rate by discipline (bottlenecks)."""
        if df.empty or 'discipline' not in df.columns:
            return go.Figure()

        discipline_stats = df.groupby('discipline').agg({
            'discipline_status': lambda x: (x == 'reprovado').sum(),
            'student_id': 'count'
        }).reset_index()

        discipline_stats.columns = ['discipline', 'failed_count', 'total_count']
        discipline_stats['failure_rate'] = (
            discipline_stats['failed_count'] / discipline_stats['total_count'] * 100
        ).round(2)

        discipline_stats = discipline_stats.sort_values('failure_rate', ascending=False).head(15)

        colors = ['#dc2626' if x > 50 else '#f59e0b' if x > 30 else '#10b981'
                  for x in discipline_stats['failure_rate']]

        fig = go.Figure(data=[
            go.Bar(
                x=discipline_stats['discipline'],
                y=discipline_stats['failure_rate'],
                text=discipline_stats['failure_rate'].apply(lambda x: f'{x:.1f}%'),
                textposition='outside',
                marker=dict(
                    color=colors,
                    line=dict(color='#ffffff', width=1)
                ),
                hovertemplate='<b>%{x}</b><br>Taxa de Reprovação: %{y:.1f}%<br>Reprovados: ' +
                              discipline_stats['failed_count'].astype(str) +
                              '<br>Total: ' + discipline_stats['total_count'].astype(str) +
                              '<extra></extra>'
            )
        ])

        fig.update_layout(
            title_font_size=18,
            title_font_family=FONT_FAMILY,
            xaxis_title='Disciplina',
            yaxis_title='Taxa de Reprovação (%)',
            font_family=FONT_FAMILY,
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=40, b=120, l=60, r=20),
            xaxis=dict(
                tickangle=-45,
                showgrid=False
            ),
            yaxis=dict(
                showgrid=True,
                gridcolor='rgba(0,0,0,0.1)',
                range=[0, min(100, max(discipline_stats['failure_rate']) * 1.2)]
            ),
            height=500
        )

        return fig

    def calculate_student_churn_risk(self, df: pd.DataFrame):
        """Calculate churn risk for each student."""
        if df.empty or 'student_id' not in df.columns:
            return pd.DataFrame()

        churn_data = []

        for student_id in df['student_id'].unique():
            student_df = df[df['student_id'] == student_id]

            churn_prob = calculate_churn_probability(student_df)
            risk_level = get_churn_risk_level(churn_prob)

            student_info = student_df.iloc[0]

            churn_data.append({
                'student_id': student_id,
                'course': student_info.get('course', 'N/A'),
                'churn_probability': churn_prob,
                'risk_level': risk_level,
                'avg_grade': student_df['final_grade'].mean(),
                'avg_attendance': student_df['attendance_pct'].mean(),
                'failed_count': (student_df['discipline_status'] == 'reprovado').sum()
            })

        return pd.DataFrame(churn_data)

    def build_churn_risk_gauge(self, df: pd.DataFrame):
        """Build gauge chart showing overall churn risk."""
        churn_df = self.calculate_student_churn_risk(df)

        if churn_df.empty:
            avg_churn = 0
        else:
            avg_churn = churn_df['churn_probability'].mean() * 100

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_churn,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Risco Médio de Evasão (%)", 'font': {'size': 18, 'family': FONT_FAMILY}},
            delta={'reference': 40, 'increasing': {'color': "red"}, 'decreasing': {'color': "green"}},
            gauge={
                'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': "darkblue"},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 40], 'color': '#d1fae5'},
                    {'range': [40, 70], 'color': '#fed7aa'},
                    {'range': [70, 100], 'color': '#fecaca'}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 70
                }
            }
        ))

        fig.update_layout(
            font={'family': FONT_FAMILY},
            paper_bgcolor='rgba(0,0,0,0)',
            height=350,
            margin=dict(t=40, b=20, l=20, r=20)
        )

        return fig

    def build_churn_risk_table(self, df: pd.DataFrame):
        """Build table showing students at high risk of churn."""
        churn_df = self.calculate_student_churn_risk(df)

        if churn_df.empty:
            return dash_table.DataTable(data=[], columns=[])

        high_risk = churn_df[churn_df['risk_level'] == 'high'].sort_values(
            'churn_probability', ascending=False
        ).head(20)

        if high_risk.empty:
            high_risk = churn_df.sort_values('churn_probability', ascending=False).head(10)

        high_risk = high_risk.copy()
        high_risk['churn_probability'] = (high_risk['churn_probability'] * 100).round(1)
        high_risk['avg_grade'] = high_risk['avg_grade'].round(2)
        high_risk['avg_attendance'] = high_risk['avg_attendance'].round(1)

        display_df = high_risk[['student_id', 'course', 'churn_probability', 'avg_grade',
                                 'avg_attendance', 'failed_count']]

        columns = [
            {'name': 'ID Aluno', 'id': 'student_id'},
            {'name': 'Curso', 'id': 'course'},
            {'name': 'Risco (%)', 'id': 'churn_probability'},
            {'name': 'Média', 'id': 'avg_grade'},
            {'name': 'Freq. (%)', 'id': 'avg_attendance'},
            {'name': 'Reprovações', 'id': 'failed_count'}
        ]

        return dash_table.DataTable(
            columns=columns,
            data=display_df.to_dict('records'),
            page_size=10,
            style_table={
                'overflowX': 'auto',
                'borderRadius': '8px'
            },
            style_header={
                'textAlign': 'center',
                'padding': '12px',
                'fontSize': '14px',
                'fontFamily': FONT_FAMILY,
                'backgroundColor': '#dc2626',
                'color': 'white',
                'fontWeight': '700',
                'border': 'none'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontSize': '13px',
                'fontFamily': FONT_FAMILY,
                'border': '1px solid #e2e8f0'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'churn_probability', 'filter_query': '{churn_probability} >= 80'},
                    'backgroundColor': '#fee2e2',
                    'color': '#991b1b',
                    'fontWeight': '700'
                },
                {
                    'if': {'column_id': 'churn_probability', 'filter_query': '{churn_probability} >= 70 && {churn_probability} < 80'},
                    'backgroundColor': '#fef3c7',
                    'color': '#92400e',
                    'fontWeight': '600'
                },
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8fafc'}
            ]
        )

    def build_course_evaluation_gauge(self, df: pd.DataFrame):
        """Build gauge chart showing average course evaluation with color indicators."""
        if df.empty or 'course_evaluation' not in df.columns:
            avg_evaluation = 0
        else:
            df_with_eval = df[df['course_evaluation'].notna()]
            if df_with_eval.empty:
                avg_evaluation = 0
            else:
                avg_evaluation = df_with_eval['course_evaluation'].mean()

        if avg_evaluation >= 6:
            bar_color = "#10b981"
            delta_color = "green"
        elif avg_evaluation >= 5.5:
            bar_color = "#f59e0b"
            delta_color = "orange"
        else:
            bar_color = "#ef4444"
            delta_color = "red"

        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=avg_evaluation,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Avaliação Média do Curso", 'font': {'size': 18, 'family': FONT_FAMILY}},
            delta={
                'reference': 6,
                'increasing': {'color': "green"},
                'decreasing': {'color': "red"},
                'suffix': ' pts'
            },
            number={'suffix': '/10', 'font': {'size': 40}},
            gauge={
                'axis': {'range': [0, 10], 'tickwidth': 1, 'tickcolor': "darkblue"},
                'bar': {'color': bar_color, 'thickness': 0.75},
                'bgcolor': "white",
                'borderwidth': 2,
                'bordercolor': "gray",
                'steps': [
                    {'range': [0, 5.5], 'color': '#fecaca'},      # Red zone - Bad
                    {'range': [5.5, 6], 'color': '#fed7aa'},      # Orange zone - Warning
                    {'range': [6, 10], 'color': '#d1fae5'}        # Green zone - Good
                ],
                'threshold': {
                    'line': {'color': "#3b82f6", 'width': 4},
                    'thickness': 0.75,
                    'value': 6
                }
            }
        ))

        fig.update_layout(
            font={'family': FONT_FAMILY},
            paper_bgcolor='rgba(0,0,0,0)',
            height=350,
            margin=dict(t=40, b=20, l=20, r=20)
        )

        return fig

    def build_statistics_cards(self, df: pd.DataFrame):
        """Build statistics summary cards."""
        if df.empty:
            return html.Div()

        total_students = df['student_id'].nunique()
        total_courses = df['course'].nunique() if 'course' in df.columns else 0
        avg_grade = df['final_grade'].mean()
        avg_attendance = df['attendance_pct'].mean()
        failure_rate = (df['discipline_status'] == 'reprovado').sum() / len(df) * 100 if len(df) > 0 else 0

        if 'course_evaluation' in df.columns:
            df_with_eval = df[df['course_evaluation'].notna()]
            avg_evaluation = df_with_eval['course_evaluation'].mean() if not df_with_eval.empty else None
        else:
            avg_evaluation = None

        if avg_evaluation is not None:
            if avg_evaluation >= 6:
                eval_color = '#10b981'
            elif avg_evaluation >= 5.5:
                eval_color = '#f59e0b'
            else:
                eval_color = '#ef4444'
        else:
            eval_color = '#94a3b8'

        cards_data = [
            {
                'title': 'Total de Alunos',
                'value': f'{total_students:,}',
                'icon': '👥',
                'color': '#3b82f6'
            },
            {
                'title': 'Cursos',
                'value': f'{total_courses:,}',
                'icon': '🎓',
                'color': '#10b981'
            },
            {
                'title': 'Média Geral',
                'value': f'{avg_grade:.2f}' if pd.notna(avg_grade) else 'N/A',
                'icon': '📊',
                'color': '#8b5cf6'
            },
            {
                'title': 'Frequência Média',
                'value': f'{avg_attendance:.1f}%' if pd.notna(avg_attendance) else 'N/A',
                'icon': '📅',
                'color': '#06b6d4'
            },
            {
                'title': 'Avaliação do Curso',
                'value': f'{avg_evaluation:.2f}/10' if avg_evaluation is not None else 'N/A',
                'icon': '⭐',
                'color': eval_color
            },
            {
                'title': 'Taxa de Reprovação',
                'value': f'{failure_rate:.1f}%',
                'icon': '⚠️',
                'color': '#ef4444'
            }
        ]

        cards = []
        for card in cards_data:
            cards.append(
                html.Div([
                    html.Div(card['icon'], style={
                        'fontSize': '36px',
                        'marginBottom': '10px'
                    }),
                    html.H3(card['value'], style={
                        'margin': '0',
                        'fontSize': '28px',
                        'fontWeight': '700',
                        'color': card['color']
                    }),
                    html.P(card['title'], style={
                        'margin': '5px 0 0 0',
                        'fontSize': '14px',
                        'color': '#64748b'
                    })
                ], style={
                    'backgroundColor': '#ffffff',
                    'padding': '20px',
                    'borderRadius': '12px',
                    'boxShadow': '0 2px 8px rgba(0,0,0,0.1)',
                    'textAlign': 'center',
                    'flex': '1',
                    'minWidth': '180px',
                    'border': f'2px solid {card["color"]}20'
                })
            )

        return html.Div(cards, style={
            'display': 'flex',
            'gap': '20px',
            'flexWrap': 'wrap',
            'marginBottom': '30px'
        })

    def build_main_data_table(self, df: pd.DataFrame):
        """Build main data table with all records."""
        if df.empty:
            return dash_table.DataTable(data=[], columns=[])

        display_cols = ['student_id', 'course', 'semester', 'discipline', 'final_grade',
                       'attendance_pct', 'discipline_status', 'payment_status',
                       'course_evaluation']

        df_display = df[display_cols].copy()
        df_display['final_grade'] = df_display['final_grade'].round(2)
        df_display['attendance_pct'] = df_display['attendance_pct'].round(1)

        columns = [
            {'name': 'ID Aluno', 'id': 'student_id'},
            {'name': 'Curso', 'id': 'course'},
            {'name': 'Período', 'id': 'semester'},
            {'name': 'Disciplina', 'id': 'discipline'},
            {'name': 'Nota Final', 'id': 'final_grade'},
            {'name': 'Frequência (%)', 'id': 'attendance_pct'},
            {'name': 'Status', 'id': 'discipline_status'},
            {'name': 'Pagamento', 'id': 'payment_status'},
            {'name': 'Aval. Curso', 'id': 'course_evaluation'}
        ]

        return dash_table.DataTable(
            columns=columns,
            data=df_display.to_dict('records'),
            page_size=20,
            sort_action='native',
            filter_action='native',
            style_table={
                'overflowX': 'auto',
                'borderRadius': '8px'
            },
            style_header={
                'textAlign': 'center',
                'padding': '12px',
                'fontSize': '14px',
                'fontFamily': FONT_FAMILY,
                'backgroundColor': '#3b82f6',
                'color': 'white',
                'fontWeight': '700',
                'border': 'none'
            },
            style_cell={
                'textAlign': 'center',
                'padding': '10px',
                'fontSize': '13px',
                'fontFamily': FONT_FAMILY,
                'border': '1px solid #e2e8f0',
                'minWidth': '100px'
            },
            style_data_conditional=[
                {
                    'if': {'column_id': 'final_grade', 'filter_query': '{final_grade} < 6'},
                    'backgroundColor': '#fee2e2',
                    'color': '#991b1b'
                },
                {
                    'if': {'column_id': 'attendance_pct', 'filter_query': '{attendance_pct} < 75'},
                    'backgroundColor': '#fef3c7',
                    'color': '#92400e'
                },
                {'if': {'row_index': 'odd'}, 'backgroundColor': '#f8fafc'}
            ]
        )
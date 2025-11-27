from dash import html, dcc

def create_layout():
    return html.Div([
        html.Div([
            html.H1("🎓 Sistema de Análise Acadêmica Universitária",
                   style={
                       "textAlign": "center",
                       "color": "#ffffff",
                       "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                       "marginBottom": "10px",
                       "fontSize": "38px",
                       "fontWeight": "700"
                   }),
            html.P("Análise de Desempenho, Frequência e Previsão de Evasão de Estudantes",
                  style={
                      "textAlign": "center",
                      "color": "#e0e7ff",
                      "fontSize": "17px",
                      "marginTop": "0",
                      "marginBottom": "30px",
                      "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
                  })
        ], style={
            "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
            "padding": "40px 20px",
            "borderRadius": "0 0 20px 20px",
            "marginBottom": "40px",
            "boxShadow": "0 4px 6px rgba(0,0,0,0.1)"
        }),

        html.Div([
            dcc.Upload(
                id="upload-csv",
                children=html.Div([
                    html.Div("📄", style={"fontSize": "48px", "marginBottom": "15px"}),
                    html.H3("Envie os dados em CSV",
                           style={
                               "margin": "0",
                               "color": "#1e293b",
                               "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                               "fontWeight": "600"
                           }),
                    html.P("Arraste o arquivo CSV aqui ou clique para selecionar",
                          style={
                              "fontSize": "15px",
                              "margin": "10px 0 5px",
                              "color": "#64748b",
                              "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
                          }),
                    html.P("Formato esperado: id_aluno, curso, periodo_letivo, disciplina, nota_final, frequencia_pct, status_pagamento, status_disciplina, nota_avaliacao_curso, status_matricula",
                          style={
                              "fontSize": "12px",
                              "margin": "5px 0 0",
                              "color": "#94a3b8",
                              "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
                              "fontStyle": "italic"
                          })
                ], style={
                    "borderRadius": "16px",
                    "textAlign": "center",
                    "backgroundColor": "#ffffff",
                    "cursor": "pointer",
                    "height": "200px",
                    "transition": "all 0.3s ease",
                    "boxShadow": "0 1px 3px rgba(0,0,0,0.1)"
                }),
                multiple=False
            ),

            html.Div(id="upload-status",
                    style={
                        "color": "#059669",
                        "fontWeight": "600",
                        "fontSize": "16px",
                        "textAlign": "center",
                        "marginTop": "20px",
                        "padding": "12px",
                        "borderRadius": "8px",
                        "backgroundColor": "#f0fdf4",
                        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
                    }),
        ], style={
            "maxWidth": "900px",
            "margin": "0 auto 40px",
            "padding": "0 20px"
        }),

        dcc.Store(id="store-data"),

        html.Div(id="dashboard-area", style={"padding": "0 20px"})
    ], style={
        "backgroundColor": "#f8fafc",
        "minHeight": "100vh",
        "fontFamily": "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    })
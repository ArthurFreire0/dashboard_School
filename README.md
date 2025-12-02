# Dashboard de Análise Acadêmica Universitária

Ferramenta simples para analisar dados acadêmicos e identificar:
- Taxa de reprovação por disciplina
- Relação entre frequência e desempenho
- Risco de evasão (churn) dos estudantes
- **Avaliação média do curso pelos alunos com indicadores de qualidade**

## Requisitos
- Python 3.13+
- uv (recomendado) ou pip

## Como executar

### Usando uv (recomendado)
```pwsh
# Criar ambiente virtual
uv venv
.venv\Scripts\activate.ps1 # No Windows
source .venv/bin/activate  # No Linux/Mac

# Instalar dependências
uv sync
uv pip install -e .

# Executar o dashboard
uv run -m dashboard_school.main
```

## Como usar
1. Faça upload do seu arquivo CSV na interface.
2. Use o `sample_data.csv` como exemplo (se disponível).
3. Explore os gráficos e tabelas para entender gargalos e riscos.

## O que o sistema mostra
- **Cartões com estatísticas gerais** (alunos, matrículas, médias, frequência, avaliação do curso, reprovação)
- **Medidor de Avaliação do Curso** - Indicador visual com cores:
  - 🟢 Verde (≥ 6): Avaliação BOA - alunos satisfeitos com o curso
  - 🟡 Amarelo (5.5 - 6): Avaliação de ALERTA - curso precisa de atenção
  - 🔴 Vermelho (< 5.5): Avaliação RUIM - curso necessita melhorias urgentes
- Gráfico de pizza por forma de ingresso
- Barras com disciplinas que têm maior taxa de reprovação
- Dispersão entre frequência (%) e nota final
- Medidor de risco médio de evasão
- Tabela de alunos com maior risco
- Tabela completa dos dados enviados

## Dicas
- Verifique se o CSV contém colunas esperadas (id_aluno, curso, periodo_letivo, disciplina, nota_final, frequencia_pct, **nota_avaliacao_curso**, etc.).
- Se houver erros, confira os logs no terminal e se as dependências estão instaladas.



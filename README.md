# Dashboard de Análise Acadêmica Universitária

Ferramenta simples para analisar dados acadêmicos e identificar:
- Taxa de reprovação por disciplina
- Relação entre frequência e desempenho
- Risco de evasão (churn) dos estudantes

## Requisitos
- Python 3.13+
- uv (recomendado) ou pip

## Como executar

### Usando uv (recomendado)
```pwsh
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
- Cartões com estatísticas gerais (alunos, matrículas, médias, frequência, reprovação)
- Gráfico de pizza por forma de ingresso
- Barras com disciplinas que têm maior taxa de reprovação
- Dispersão entre frequência (%) e nota final
- Medidor de risco médio de evasão
- Tabela de alunos com maior risco
- Tabela completa dos dados enviados

## Dicas
- Verifique se o CSV contém colunas esperadas (id_aluno, curso, periodo_letivo, disciplina, nota_final, frequencia_pct, etc.).
- Se houver erros, confira os logs no terminal e se as dependências estão instaladas.

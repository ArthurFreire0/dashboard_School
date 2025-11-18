import os
import base64
import traceback
from dash import Dash, Input, Output, State

from src.dashboard_school.components.layout import create_layout
from processing import (
    try_read_csv_bytes,
    process_raw_dataframe_to_standard
)
from components.dashboard import DashboardBuilder

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Dash(__name__)
app.title = "Dashboard Escolar"
app.layout = create_layout()

dashboard = DashboardBuilder()


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
        df_std = process_raw_dataframe_to_standard(df_raw)

        return f"Arquivo '{filename}' processado com sucesso!", df_std.to_dict("records")

    except ValueError:
        traceback.print_exc()
        return "Conteúdo do arquivo inválido ou formato não suportado.", []

    except UnicodeDecodeError as e:
        traceback.print_exc()
        return f"Erro ao processar arquivo: {e}", []


@app.callback(
    Output("dashboard-area", "children"),
    Input("store-data", "data")
)
def update_dashboard(store_data):
    return dashboard.render_dashboard(store_data)


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=3000)

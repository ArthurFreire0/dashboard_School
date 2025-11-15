
import io
import unicodedata
import pandas as pd
import numpy as np
from typing import List, Optional

MEDIA_APROVACAO = 6.0
DEFAULT_AULAS_TOTAIS = 200

SUBJECT_KEYS = [
    "matematica", "portugues", "ingles", "ciencias",
    "historia", "geografia", "artes"
]

STANDARD_COLS = [
    "nome", "turma", "serie",
] + SUBJECT_KEYS + [
    "media_geral", "faltas", "aulas_ano", "presenca", "status"
]



# UTILIDADES

def remove_accents(text: str) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def normalize_str(s: object) -> str:
    if pd.isna(s):
        return ""
    s = str(s)
    s = s.replace("\ufeff", "").strip()
    s = remove_accents(s).lower()
    s = s.replace("\t", " ").replace("-", " ").replace("_", " ")
    return " ".join(s.split())


def clean_cols(cols: List[str]) -> List[str]:
    return [normalize_str(c) for c in cols]


def try_read_csv_bytes(b: bytes) -> pd.DataFrame:
    stream = io.BytesIO(b)
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]

    for enc in encodings:
        try:
            stream.seek(0)
            df = pd.read_csv(stream, sep=None, engine="python", encoding=enc)
            df.columns = clean_cols(df.columns.tolist())
            return df
        except Exception:
            pass

    stream.seek(0)
    df = pd.read_csv(stream, sep=";", engine="python", encoding="utf-8")
    df.columns = clean_cols(df.columns.tolist())
    return df


def normalize_col_for_match(c: str) -> str:
    return normalize_str(c).replace(" ", "")


def detect_subject_columns(columns: List[str]):
    mapping = {k: [] for k in SUBJECT_KEYS}
    col_map = {c: normalize_col_for_match(c) for c in columns}

    for orig, norm in col_map.items():
        for subj in SUBJECT_KEYS:
            subj_norm = subj.replace(" ", "")
            if subj_norm in norm and "media" not in norm:
                mapping[subj].append(orig)
            elif norm.startswith(subj_norm[:3]):
                mapping[subj].append(orig)

    for k in mapping:
        mapping[k] = list(dict.fromkeys(mapping[k]))

    return mapping


def clean_series_value(s) -> Optional[str]:
    if pd.isna(s):
        return None
    s2 = normalize_str(s)
    s2 = s2.replace("serie", "").replace("ano", "").replace(".0", "").strip()
    return None if s2 in ["", "nan", "none"] else s2


def find_col_like(columns: List[str], keywords: List[str]) -> Optional[str]:
    cols_norm = {c: normalize_str(c) for c in columns}
    for kw in keywords:
        kwn = normalize_str(kw)
        for orig, norm in cols_norm.items():
            if kwn in norm:
                return orig
    return None



# PROCESSAMENTO PRINCIPAL


def process_raw_df_to_standard(df_raw: pd.DataFrame) -> pd.DataFrame:
    original_cols = list(df_raw.columns)

    nome_col = find_col_like(original_cols, ["nome", "aluno", "name"])
    turma_col = find_col_like(original_cols, ["turma", "sala", "classe"])
    serie_col = find_col_like(original_cols, ["serie", "ano"])

    if nome_col is None or turma_col is None:
        raise ValueError("CSV precisa conter colunas de NOME e TURMA.")

    df_clean = df_raw.copy()

    for c in df_clean.columns:
        df_clean[c] = (
            df_clean[c].astype(str)
            .str.replace(",", ".")
            .str.strip()
        )

    subj_map = detect_subject_columns(list(df_clean.columns))

    df_out = pd.DataFrame()
    df_out["nome"] = df_clean[nome_col]
    df_out["turma"] = df_clean[turma_col]
    df_out["serie"] = df_clean[serie_col].apply(clean_series_value) if serie_col else None

    for subj in SUBJECT_KEYS:
        cols = subj_map.get(subj, [])
        if cols:
            df_out[subj] = df_clean[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1).round(1)
        else:
            df_out[subj] = np.nan

    df_out["media_geral"] = df_out[SUBJECT_KEYS].mean(axis=1).round(1)

    # faltas e aulas
    faltas_col = find_col_like(original_cols, ["falta"])
    aulas_col = find_col_like(original_cols, ["aulas", "aulas tot", "carga horaria"])

    df_out["faltas"] = pd.to_numeric(df_clean[faltas_col], errors="coerce") if faltas_col else np.nan
    df_out["aulas_ano"] = pd.to_numeric(df_clean[aulas_col], errors="coerce") if aulas_col else DEFAULT_AULAS_TOTAIS

    # presença
    mask = (
        df_out["faltas"].notna()
        & df_out["aulas_ano"].notna()
        & (df_out["aulas_ano"] != 0)
    )
    df_out["presenca"] = np.where(mask,
                                  ((1 - df_out["faltas"] / df_out["aulas_ano"]) * 100).round(1),
                                  np.nan)

    df_out["status"] = df_out["media_geral"].apply(lambda x: "Aprovado" if x >= MEDIA_APROVACAO else "Reprovado")

    for c in STANDARD_COLS:
        if c not in df_out.columns:
            df_out[c] = np.nan

    return df_out[STANDARD_COLS].reset_index(drop=True)

# python
import io
import unicodedata
import pandas as pd
import numpy as np
from typing import List, Optional

PASSING_AVERAGE = 6.0
DEFAULT_TOTAL_CLASSES = 200

SUBJECT_KEYS = [
    "matematica", "portugues", "ingles", "ciencias",
    "historia", "geografia", "artes"
]

STANDARD_COLS = [
    "nome", "turma", "serie",
] + SUBJECT_KEYS + [
    "media_geral", "faltas", "aulas_ano", "presenca", "status"
]


def remove_accents(text: str) -> str:
    if text is None:
        return ""
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def normalize_str(value: object) -> str:
    if pd.isna(value):
        return ""
    s = str(value)
    s = s.replace("\ufeff", "").strip()
    s = remove_accents(s).lower()
    s = s.replace("\t", " ").replace("-", " ").replace("_", " ")
    return " ".join(s.split())


def clean_columns(columns: List[str]) -> List[str]:
    return [normalize_str(c) for c in columns]


def try_read_csv_bytes(data: bytes) -> pd.DataFrame:
    stream = io.BytesIO(data)
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252"]

    for enc in encodings:
        try:
            stream.seek(0)
            df = pd.read_csv(stream, sep=None, engine="python", encoding=enc)
            df.columns = clean_columns(df.columns.tolist())
            return df
        except Exception:
            pass

    stream.seek(0)
    df = pd.read_csv(stream, sep=";", engine="python", encoding="utf-8")
    df.columns = clean_columns(df.columns.tolist())
    return df


def normalize_column_for_match(column: str) -> str:
    return normalize_str(column).replace(" ", "")


def detect_subject_columns(columns: List[str]):
    mapping = {k: [] for k in SUBJECT_KEYS}
    col_map = {c: normalize_column_for_match(c) for c in columns}

    for original, normalized in col_map.items():
        for subject in SUBJECT_KEYS:
            subject_norm = subject.replace(" ", "")
            if subject_norm in normalized and "media" not in normalized:
                mapping[subject].append(original)
            elif normalized.startswith(subject_norm[:3]):
                mapping[subject].append(original)

    for k in mapping:
        mapping[k] = list(dict.fromkeys(mapping[k]))

    return mapping


def clean_grade_level_value(value) -> Optional[str]:
    if pd.isna(value):
        return None
    s2 = normalize_str(value)
    s2 = s2.replace("serie", "").replace("ano", "").replace(".0", "").strip()
    return None if s2 in ["", "nan", "none"] else s2


def find_column_like(columns: List[str], keywords: List[str]) -> Optional[str]:
    columns_normalized = {c: normalize_str(c) for c in columns}
    for kw in keywords:
        kw_normalized = normalize_str(kw)
        for original, normalized in columns_normalized.items():
            if kw_normalized in normalized:
                return original
    return None


def process_raw_dataframe_to_standard(raw_df: pd.DataFrame) -> pd.DataFrame:
    original_columns = list(raw_df.columns)

    name_column = find_column_like(original_columns, ["nome", "aluno", "name"])
    class_column = find_column_like(original_columns, ["turma", "sala", "classe"])
    grade_level_column = find_column_like(original_columns, ["serie", "ano"])

    if name_column is None or class_column is None:
        raise ValueError("CSV precisa conter colunas de NOME e TURMA.")

    cleaned_df = raw_df.copy()

    for col in cleaned_df.columns:
        cleaned_df[col] = (
            cleaned_df[col].astype(str)
            .str.replace(",", ".")
            .str.strip()
        )

    subject_map = detect_subject_columns(list(cleaned_df.columns))

    output_df = pd.DataFrame()
    output_df["nome"] = cleaned_df[name_column]
    output_df["turma"] = cleaned_df[class_column]
    output_df["serie"] = cleaned_df[grade_level_column].apply(clean_grade_level_value) if grade_level_column else None

    for subject in SUBJECT_KEYS:
        cols = subject_map.get(subject, [])
        if cols:
            output_df[subject] = cleaned_df[cols].apply(pd.to_numeric, errors="coerce").mean(axis=1).round(1)
        else:
            output_df[subject] = np.nan

    output_df["media_geral"] = output_df[SUBJECT_KEYS].mean(axis=1).round(1)

    absences_column = find_column_like(original_columns, ["falta"])
    total_classes_column = find_column_like(original_columns, ["aulas", "aulas tot", "carga horaria"])

    output_df["faltas"] = pd.to_numeric(cleaned_df[absences_column], errors="coerce") if absences_column else np.nan
    output_df["aulas_ano"] = (
        pd.to_numeric(cleaned_df[total_classes_column], errors="coerce")
        if total_classes_column else DEFAULT_TOTAL_CLASSES
    )

    presence_mask = (
        output_df["faltas"].notna()
        & output_df["aulas_ano"].notna()
        & (output_df["aulas_ano"] != 0)
    )
    output_df["presenca"] = np.where(
        presence_mask,
        ((1 - output_df["faltas"] / output_df["aulas_ano"]) * 100).round(1),
        np.nan
    )

    output_df["status"] = output_df["media_geral"].apply(
        lambda x: "Aprovado" if x >= PASSING_AVERAGE else "Reprovado"
    )

    for col in STANDARD_COLS:
        if col not in output_df.columns:
            output_df[col] = np.nan

    return output_df[STANDARD_COLS].reset_index(drop=True)
import pandas as pd
import numpy as np
import io
import unicodedata
import re

PASSING_GRADE = 6.0
MINIMUM_ATTENDANCE = 75.0


def remove_accents(text: str) -> str:
    """Remove accents from text."""
    if not isinstance(text, str):
        text = str(text)
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join([c for c in nfkd if not unicodedata.combining(c)])


def normalize_str(value: object) -> str:
    """Normalize string values for comparison."""
    if pd.isna(value):
        return ""
    s = str(value)
    s = s.replace("\ufeff", "").strip()
    s = remove_accents(s).lower()
    s = s.replace("\t", " ").replace("-", "_")
    # Replace multiple consecutive spaces with single underscore
    s = re.sub(r'\s+', '_', s)
    return s


def try_read_csv_bytes(data: bytes) -> pd.DataFrame:
    """Try to read CSV from bytes using different encodings and separators."""
    stream = io.BytesIO(data)
    encodings = ["utf-8-sig", "utf-8", "latin1", "cp1252", "iso-8859-1"]
    separators = [",", ";", "\t"]

    for encoding in encodings:
        for sep in separators:
            try:
                stream.seek(0)
                df = pd.read_csv(stream, sep=sep, encoding=encoding, engine="python")

                # Check if we got valid data (more than 1 column)
                if len(df.columns) > 1:
                    print(f"✅ Successfully read CSV with encoding={encoding}, separator='{sep}'")
                    return df
            except Exception as e:
                continue

    # Last resort - try default pandas read
    stream.seek(0)
    return pd.read_csv(stream)


def map_admission_type(value) -> str:
    """Map admission type to standard format."""
    if pd.isna(value):
        return "vestibular"

    normalized = normalize_str(value)

    if "externa" in normalized or "external" in normalized:
        return "transferencia_externa"
    elif "interna" in normalized or "internal" in normalized:
        return "transferencia_interna"
    elif "bolsa" in normalized or "scholarship" in normalized or "promocao" in normalized:
        return "bolsista"
    elif "vestibular" in normalized or "entrance" in normalized:
        return "vestibular"
    else:
        return "vestibular"


def map_enrollment_status(value) -> str:
    """Map enrollment status to standard format."""
    if pd.isna(value):
        return "ativo"

    normalized = normalize_str(value)

    if "evadido" in normalized or "dropped" in normalized or "desistente" in normalized:
        return "evadido"
    elif "trancado" in normalized or "suspended" in normalized or "trancamento" in normalized:
        return "trancado"
    elif "ativo" in normalized or "active" in normalized or "matriculado" in normalized:
        return "ativo"
    else:
        return "ativo"


def map_discipline_status(value) -> str:
    """Map discipline status to standard format."""
    if pd.isna(value):
        return "em_andamento"

    normalized = normalize_str(value)

    if "aprovado" in normalized or "approved" in normalized or "passed" in normalized:
        return "aprovado"
    elif "reprovado" in normalized or "failed" in normalized or "reprovacao" in normalized:
        return "reprovado"
    elif "andamento" in normalized or "progress" in normalized or "cursando" in normalized:
        return "em_andamento"
    else:
        return "em_andamento"


def map_payment_status(value) -> str:
    """Map payment status to standard format."""
    if pd.isna(value):
        return "pendente"

    normalized = normalize_str(value)

    if "pago" in normalized or "paid" in normalized or "quitado" in normalized:
        return "pago"
    elif "atrasado" in normalized or "overdue" in normalized or "late" in normalized or "vencido" in normalized:
        return "atrasado"
    elif "pendente" in normalized or "pending" in normalized:
        return "pendente"
    else:
        return "pendente"


def process_university_data(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    df.columns = [normalize_str(col) for col in df.columns]

    column_mapping = {}
    for col in df.columns:
        col_lower = col.lower()
        if ("avaliacao" in col_lower and "curso" in col_lower) or "nota_avaliacao_curso" in col_lower:
            column_mapping[col] = "course_evaluation"
        elif ("nota" in col_lower and "final" in col_lower) or col_lower == "nota_final":
            column_mapping[col] = "final_grade"
        elif "id" in col_lower and "aluno" in col_lower:
            column_mapping[col] = "student_id"
        elif "curso" in col_lower and "avaliacao" not in col_lower:
            column_mapping[col] = "course"
        elif "periodo" in col_lower or "semestre" in col_lower or "letivo" in col_lower:
            column_mapping[col] = "semester"
        elif "disciplina" in col_lower and "status" not in col_lower:
            column_mapping[col] = "discipline"
        elif "frequencia" in col_lower or "attendance" in col_lower:
            column_mapping[col] = "attendance_pct"
        elif ("status" in col_lower and "pagamento" in col_lower) or "pagamento" in col_lower:
            column_mapping[col] = "payment_status"
        elif "status" in col_lower and "disciplina" in col_lower:
            column_mapping[col] = "discipline_status"
        elif ("avaliacao" in col_lower and "curso" in col_lower) or ("nota" in col_lower and "curso" in col_lower):
            # Redundant rule retained for robustness but will be overridden by the first condition
            column_mapping[col] = "course_evaluation"
        elif "status" in col_lower and "matricula" in col_lower:
            column_mapping[col] = "enrollment_status"
        elif "forma" in col_lower and "ingresso" in col_lower:
            column_mapping[col] = "admission_type"
        elif "ingresso" in col_lower or "admission" in col_lower:
            column_mapping[col] = "admission_type"
        elif col_lower == "nota":
            column_mapping[col] = "final_grade"

    df = df.rename(columns=column_mapping)

    for target in ["final_grade", "attendance_pct", "course_evaluation"]:
        if (target in df.columns) and isinstance(df[target], pd.DataFrame):
            temp = df[target]
            df[target] = temp.apply(lambda row: next((x for x in row if pd.notna(x)), np.nan), axis=1)

    required = ["student_id", "course", "semester", "discipline", "final_grade",
                "attendance_pct", "payment_status", "discipline_status",
                "course_evaluation", "enrollment_status"]

    for col in required:
        if col not in df.columns:
            df[col] = np.nan

    if "admission_type" not in df.columns:
        df["admission_type"] = "vestibular"

    df["student_id"] = df["student_id"].astype(str)
    df["course"] = df["course"].astype(str)
    df["semester"] = df["semester"].astype(str)
    df["discipline"] = df["discipline"].astype(str)

    for num_col in ["final_grade", "attendance_pct", "course_evaluation"]:
        if isinstance(df[num_col], pd.DataFrame):
            df[num_col] = df[num_col].apply(lambda row: next((x for x in row if pd.notna(x)), np.nan), axis=1)
        df[num_col] = pd.to_numeric(df[num_col], errors="coerce")

    df["admission_type"] = df["admission_type"].apply(map_admission_type)
    df["enrollment_status"] = df["enrollment_status"].apply(map_enrollment_status)
    df["discipline_status"] = df["discipline_status"].apply(map_discipline_status)
    df["payment_status"] = df["payment_status"].apply(map_payment_status)

    df["is_passing"] = (df["final_grade"] >= PASSING_GRADE) & (df["attendance_pct"] >= MINIMUM_ATTENDANCE)
    df["at_risk"] = (
        (df["final_grade"] < PASSING_GRADE) |
        (df["attendance_pct"] < MINIMUM_ATTENDANCE) |
        (df["payment_status"] == "atrasado")
    )

    return df


def calculate_churn_probability(student_data: pd.DataFrame) -> float:
    """Calculate churn probability for a student based on their records."""
    if student_data.empty:
        return 0.0

    risk_score = 0.0

    avg_grade = student_data["final_grade"].mean()
    if pd.notna(avg_grade):
        if avg_grade < 4.0:
            risk_score += 30
        elif avg_grade < 6.0:
            risk_score += 20
        elif avg_grade < 7.0:
            risk_score += 10

    avg_attendance = student_data["attendance_pct"].mean()
    if pd.notna(avg_attendance):
        if avg_attendance < 50:
            risk_score += 25
        elif avg_attendance < 75:
            risk_score += 15
        elif avg_attendance < 85:
            risk_score += 5

    payment_issues = (student_data["payment_status"] == "atrasado").sum()
    total_records = len(student_data)
    payment_issue_rate = payment_issues / total_records if total_records > 0 else 0
    risk_score += payment_issue_rate * 20

    failed_count = (student_data["discipline_status"] == "reprovado").sum()
    fail_rate = failed_count / total_records if total_records > 0 else 0
    risk_score += fail_rate * 15

    avg_evaluation = student_data["course_evaluation"].mean()
    if pd.notna(avg_evaluation):
        if avg_evaluation <= 3:
            risk_score += 10
        elif avg_evaluation <= 5:
            risk_score += 5

    churn_probability = min(risk_score / 100, 1.0)

    return churn_probability


def get_churn_risk_level(probability: float) -> str:
    """Get risk level based on churn probability."""
    if probability >= 0.7:
        return "high"
    elif probability >= 0.4:
        return "medium"
    else:
        return "low"

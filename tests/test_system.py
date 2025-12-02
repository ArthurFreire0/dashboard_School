import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dashboard_school.modules.models import Base
from dashboard_school.processing import try_read_csv_bytes, process_university_data


@pytest.fixture
def test_db_engine():
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def test_session(test_db_engine):
    TestSession = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine
    ))
    session = TestSession()
    yield session
    session.close()
    TestSession.remove()


@pytest.fixture
def complete_csv_data():
    data = {
        'id_aluno': ['S001', 'S002', 'S003', 'S001', 'S002', 'S004'],
        'curso': ['Engenharia de Software', 'Medicina', 'Direito', 'Engenharia de Software', 'Medicina', 'Administração'],
        'periodo_letivo': ['2024.1', '2024.1', '2024.1', '2024.1', '2024.1', '2024.1'],
        'disciplina': ['Algoritmos', 'Anatomia I', 'Direito Civil', 'Banco de Dados', 'Fisiologia', 'Marketing'],
        'nota_final': [8.5, 9.0, 5.0, 7.5, 8.0, 6.5],
        'frequencia_pct': [90.0, 95.0, 60.0, 85.0, 90.0, 75.0],
        'status_pagamento': ['pago', 'pago', 'atrasado', 'pago', 'pendente', 'pago'],
        'status_disciplina': ['aprovado', 'aprovado', 'reprovado', 'aprovado', 'em_andamento', 'aprovado'],
        'nota_avaliacao_curso': [9, 10, 6, 8, 9, 7],
        'status_matricula': ['ativo', 'ativo', 'evadido', 'ativo', 'ativo', 'trancado'],
        'forma_ingresso': ['vestibular', 'vestibular', 'transferencia_externa', 'vestibular', 'bolsista', 'vestibular']
    }
    return pd.DataFrame(data)


class TestEndToEndWorkflow:
    def test_data_quality_after_processing(self, complete_csv_data):
        processed_df = process_university_data(complete_csv_data)

        assert processed_df['student_id'].notna().all()

        assert (processed_df['final_grade'] >= 0).all()
        assert (processed_df['final_grade'] <= 10).all()
        assert (processed_df['attendance_pct'] >= 0).all()
        assert (processed_df['attendance_pct'] <= 100).all()

        valid_payment_statuses = ['pago', 'pendente', 'atrasado']
        assert processed_df['payment_status'].isin(valid_payment_statuses).all()

        valid_enrollment = ['ativo', 'evadido', 'trancado']
        assert processed_df['enrollment_status'].isin(valid_enrollment).all()

    def test_csv_encoding_handling(self):
        csv_content = """id_aluno,curso,periodo_letivo,disciplina,nota_final,frequencia_pct,status_pagamento,status_disciplina,nota_avaliacao_curso,status_matricula
A001,Engenharia,2024.1,Cálculo,8.0,90.0,pago,aprovado,8,ativo"""

        utf8_bytes = csv_content.encode('utf-8')
        df = try_read_csv_bytes(utf8_bytes)
        assert len(df) == 1
        assert 'A001' in df.iloc[0].values

        latin1_bytes = csv_content.encode('latin1')
        df = try_read_csv_bytes(latin1_bytes)
        assert len(df) == 1

    def test_csv_separator_handling(self):
        csv_semicolon = """id_aluno;curso;periodo_letivo;disciplina;nota_final
A001;Engenharia;2024.1;Cálculo;8.0"""

        df = try_read_csv_bytes(csv_semicolon.encode('utf-8'))
        assert len(df.columns) > 1

        csv_tab = """id_aluno\tcurso\tperiodo_letivo\tdisciplina\tnota_final
A001\tEngenharia\t2024.1\tCálculo\t8.0"""

        df = try_read_csv_bytes(csv_tab.encode('utf-8'))
        assert len(df.columns) > 1
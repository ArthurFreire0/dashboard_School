import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from dashboard_school.modules.models import (
    Base, Student, Discipline, Grade,
    EnrollmentStatusEnum, DisciplineStatusEnum,
    PaymentStatusEnum, AdmissionTypeEnum
)

@pytest.fixture
def test_db_session():
    engine = create_engine('sqlite:///:memory:', echo=False)
    Base.metadata.create_all(bind=engine)

    TestSession = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine
    ))

    session = TestSession()
    yield session

    session.close()
    TestSession.remove()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def sample_csv_data():
    data = {
        'id_aluno': ['A001', 'A002', 'A003', 'A001'],
        'curso': ['Engenharia', 'Medicina', 'Direito', 'Engenharia'],
        'periodo_letivo': ['2024.1', '2024.1', '2024.1', '2024.1'],
        'disciplina': ['Cálculo I', 'Anatomia', 'Direito Civil', 'Física I'],
        'nota_final': [7.5, 8.0, 5.5, 9.0],
        'frequencia_pct': [85.0, 90.0, 70.0, 95.0],
        'status_pagamento': ['pago', 'pago', 'atrasado', 'pago'],
        'status_disciplina': ['aprovado', 'aprovado', 'reprovado', 'aprovado'],
        'nota_avaliacao_curso': [8, 9, 7, 8],
        'status_matricula': ['ativo', 'ativo', 'evadido', 'ativo'],
        'forma_ingresso': ['vestibular', 'vestibular', 'transferencia_externa', 'vestibular']
    }
    return pd.DataFrame(data)


class TestDatabaseIntegration:
    def test_create_student(self, test_db_session):
        student = Student(
            student_id='TEST001',
            name='Test Student',
            course='Computer Science',
            admission_type=AdmissionTypeEnum.ENTRANCE_EXAM,
            enrollment_status=EnrollmentStatusEnum.ACTIVE
        )
        test_db_session.add(student)
        test_db_session.commit()

        retrieved = test_db_session.query(Student).filter_by(student_id='TEST001').first()
        assert retrieved is not None
        assert retrieved.name == 'Test Student'
        assert retrieved.course == 'Computer Science'
        assert retrieved.admission_type == AdmissionTypeEnum.ENTRANCE_EXAM

    def test_create_discipline(self, test_db_session):
        discipline = Discipline(
            name='Advanced Mathematics',
            code='MATH301'
        )
        test_db_session.add(discipline)
        test_db_session.commit()

        retrieved = test_db_session.query(Discipline).filter_by(code='MATH301').first()
        assert retrieved is not None
        assert retrieved.name == 'Advanced Mathematics'

    def test_create_grade_with_relationships(self, test_db_session):
        student = Student(
            student_id='STU001',
            course='Engineering',
            admission_type=AdmissionTypeEnum.ENTRANCE_EXAM,
            enrollment_status=EnrollmentStatusEnum.ACTIVE
        )
        test_db_session.add(student)
        discipline = Discipline(name='Calculus I')
        test_db_session.add(discipline)
        test_db_session.flush()

        grade = Grade(
            student_id=student.id,
            discipline_id=discipline.id,
            semester='2024.1',
            final_grade=8.5,
            attendance_pct=90.0,
            payment_status=PaymentStatusEnum.PAID,
            discipline_status=DisciplineStatusEnum.APPROVED,
            course_evaluation=9
        )
        test_db_session.add(grade)
        test_db_session.commit()

        retrieved_grade = test_db_session.query(Grade).first()
        assert retrieved_grade.student.student_id == 'STU001'
        assert retrieved_grade.discipline.name == 'Calculus I'
        assert retrieved_grade.final_grade == 8.5
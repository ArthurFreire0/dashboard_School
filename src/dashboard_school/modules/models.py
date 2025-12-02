from sqlalchemy import (
    Column, Integer, String, Float,
    DateTime, ForeignKey, Enum
)
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime
from zoneinfo import ZoneInfo
import enum

Base = declarative_base()
LOCAL_TZ = ZoneInfo("America/Bahia")


class EnrollmentStatusEnum(enum.Enum):
    """Student enrollment status"""
    ACTIVE = "ativo"
    DROPPED = "evadido"
    SUSPENDED = "trancado"


class DisciplineStatusEnum(enum.Enum):
    """Discipline status"""
    APPROVED = "aprovado"
    FAILED = "reprovado"
    IN_PROGRESS = "em_andamento"


class PaymentStatusEnum(enum.Enum):
    """Payment status"""
    PAID = "pago"
    PENDING = "pendente"
    OVERDUE = "atrasado"


class AdmissionTypeEnum(enum.Enum):
    """Type of student admission"""
    EXTERNAL_TRANSFER = "transferencia_externa"
    INTERNAL_TRANSFER = "transferencia_interna"
    SCHOLARSHIP = "bolsista"
    ENTRANCE_EXAM = "vestibular"


class Student(Base):
    """Student model"""
    __tablename__ = 'students'

    id = Column(Integer, primary_key=True)
    student_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(200))
    course = Column(String(200))
    admission_type = Column(Enum(AdmissionTypeEnum))
    enrollment_status = Column(Enum(EnrollmentStatusEnum))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ), onupdate=lambda: datetime.now(LOCAL_TZ))

    grades = relationship("Grade", back_populates="student", cascade="all, delete-orphan")


class Discipline(Base):
    """Discipline/Subject model"""
    __tablename__ = 'disciplines'

    id = Column(Integer, primary_key=True)
    name = Column(String(200), unique=True, nullable=False)
    code = Column(String(50))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ))

    grades = relationship("Grade", back_populates="discipline")


class Grade(Base):
    """Student grades and attendance model"""
    __tablename__ = 'grades'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    discipline_id = Column(Integer, ForeignKey('disciplines.id'), nullable=False)
    semester = Column(String(20))
    final_grade = Column(Float)
    attendance_pct = Column(Float)
    payment_status = Column(Enum(PaymentStatusEnum))
    discipline_status = Column(Enum(DisciplineStatusEnum))
    course_evaluation = Column(Integer)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ), onupdate=lambda: datetime.now(LOCAL_TZ))

    student = relationship("Student", back_populates="grades")
    discipline = relationship("Discipline", back_populates="grades")


class ChurnPrediction(Base):
    """Churn prediction results"""
    __tablename__ = 'churn_predictions'

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    prediction_date = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ))
    churn_probability = Column(Float)
    risk_level = Column(String(20))
    factors = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(LOCAL_TZ))

# ============================================================================
# ФАЙЛ: models/dao.py
# Описание: Объектно-реляционное отображение таблиц БД
# ============================================================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    Float, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

# Базовый класс для всех моделей
Base = declarative_base()


class UserRole(enum.Enum):
    """Перечисление ролей пользователей"""
    HR = "HR"
    CANDIDATE = "Кандидат"


class VacancyStatus(enum.Enum):
    """Статусы вакансий"""
    OPEN = "Открыта"
    CLOSED = "Закрыта"
    ON_HOLD = "На паузе"


# ============================================================================
# ЕДИНАЯ ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ (для авторизации)
# ============================================================================

class User(Base):
    """
    Единая таблица пользователей для авторизации.
    Содержит HR и Кандидатов.
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Отношения
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="hr", cascade="all, delete-orphan")
    interviews_stage1_as_candidate = relationship(
        "InterviewStage1", 
        foreign_keys="InterviewStage1.candidate_id",
        back_populates="candidate", 
        cascade="all, delete-orphan"
    )
    interviews_stage1_as_hr = relationship(
        "InterviewStage1",
        foreign_keys="InterviewStage1.hr_id", 
        back_populates="hr",
        cascade="all, delete-orphan"
    )
    interviews_stage2_as_candidate = relationship(
        "InterviewStage2",
        foreign_keys="InterviewStage2.candidate_id",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )
    interviews_stage2_as_hr = relationship(
        "InterviewStage2",
        foreign_keys="InterviewStage2.hr_id",
        back_populates="hr",
        cascade="all, delete-orphan"
    )
    reports_as_candidate = relationship(
        "CandidateReport",
        foreign_keys="CandidateReport.candidate_id",
        back_populates="candidate",
        cascade="all, delete-orphan"
    )
    reports_as_hr = relationship(
        "CandidateReport",
        foreign_keys="CandidateReport.hr_id",
        back_populates="hr",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, login='{self.login}', role='{self.role.value}')>"


# ============================================================================
# РЕЗЮМЕ
# ============================================================================

class Resume(Base):
    """
    Резюме кандидата.
    Связано один-к-одному с User (где role=CANDIDATE).
    """
    __tablename__ = 'resumes'

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    
    # Личные данные
    birth_date = Column(Date)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Профессиональная информация
    education = Column(Text)
    work_experience = Column(Text)
    skills = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship("User", back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume(id={self.resume_id}, user_id={self.user_id})>"


# ============================================================================
# ВАКАНСИИ
# ============================================================================

class Vacancy(Base):
    """
    Вакансия, созданная HR-менеджером.
    Содержит вопросы для собеседования.
    """
    __tablename__ = 'vacancies'

    vacancy_id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    position_title = Column(String(100), nullable=False)
    job_description = Column(Text)
    requirements = Column(Text)
    status = Column(SQLEnum(VacancyStatus), default=VacancyStatus.OPEN)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr = relationship("User", back_populates="vacancies")
    interviews_stage1 = relationship("InterviewStage1", back_populates="vacancy", cascade="all, delete-orphan")
    interviews_stage2 = relationship("InterviewStage2", back_populates="vacancy", cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="vacancy", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vacancy(id={self.vacancy_id}, title='{self.position_title}', status='{self.status.value}')>"


# ============================================================================
# СОБЕСЕДОВАНИЯ
# ============================================================================

class InterviewStage1(Base):
    """
    Первый этап собеседования - оценка soft skills.
    """
    __tablename__ = 'interview_stage1'

    interview1_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=False)
    questions = Column(Text, comment="Вопросы заданные на собеседовании")
    candidate_answers = Column(Text, comment="Ответы кандидата")
    soft_skills_score = Column(Integer, comment="Оценка soft skills 0-100")
    confidence_score = Column(Integer, comment="Оценка уверенности 0-100")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="interviews_stage1_as_candidate")
    hr = relationship("User", foreign_keys=[hr_id], back_populates="interviews_stage1_as_hr")
    vacancy = relationship("Vacancy", back_populates="interviews_stage1")
    stage2 = relationship("InterviewStage2", back_populates="stage1", uselist=False, cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="interview1")

    def __repr__(self) -> str:
        return f"<InterviewStage1(id={self.interview1_id}, candidate_id={self.candidate_id})>"


class InterviewStage2(Base):
    """
    Второй этап собеседования - техническая оценка (hard skills).
    """
    __tablename__ = 'interview_stage2'

    interview2_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=False)
    technical_tasks = Column(Text, comment="Технические задания")
    candidate_solutions = Column(Text, comment="Решения кандидата")
    hard_skills_score = Column(Integer, comment="Оценка hard skills 0-100")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="interviews_stage2_as_candidate")
    hr = relationship("User", foreign_keys=[hr_id], back_populates="interviews_stage2_as_hr")
    stage1 = relationship("InterviewStage1", back_populates="stage2")
    vacancy = relationship("Vacancy", back_populates="interviews_stage2")
    reports = relationship("CandidateReport", back_populates="interview2")

    def __repr__(self) -> str:
        return f"<InterviewStage2(id={self.interview2_id}, candidate_id={self.candidate_id})>"


# ============================================================================
# ОТЧЕТЫ
# ============================================================================

class CandidateReport(Base):
    """
    Итоговый отчет по кандидату.
    Генерируется после прохождения собеседований.
    """
    __tablename__ = 'candidate_reports'

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'))
    interview2_id = Column(Integer, ForeignKey('interview_stage2.interview2_id'))
    
    generation_date = Column(DateTime, default=datetime.utcnow)
    final_score = Column(Float, comment="Итоговая оценка 0-100")
    hr_recommendations = Column(Text, comment="Рекомендации HR")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="reports_as_candidate")
    hr = relationship("User", foreign_keys=[hr_id], back_populates="reports_as_hr")
    vacancy = relationship("Vacancy", back_populates="reports")
    interview1 = relationship("InterviewStage1", back_populates="reports")
    interview2 = relationship("InterviewStage2", back_populates="reports")

    def __repr__(self) -> str:
        return f"<CandidateReport(id={self.report_id}, candidate_id={self.candidate_id}, score={self.final_score})>"
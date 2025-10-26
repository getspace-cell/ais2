#Объектно-реляционное отображение таблиц БД

from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    create_engine, Column, Integer, String, Text, Date, DateTime,
    Float, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
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


class User(Base):
    """
    Модель пользователя системы.
    Может быть HR-менеджером или кандидатом.
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr_profile = relationship("HRProfile", back_populates="user", uselist=False)
    resume = relationship("Resume", back_populates="user", uselist=False)
    interviews_stage1 = relationship("InterviewStage1", back_populates="candidate")
    interviews_stage2 = relationship("InterviewStage2", back_populates="candidate")
    reports = relationship("CandidateReport", back_populates="candidate")

    def __repr__(self) -> str:
        return f"<User(id={self.user_id}, login='{self.login}', role='{self.role.value}')>"


class HRProfile(Base):
    """
    Профиль HR-менеджера.
    Связан с пользователем с ролью HR.
    """
    __tablename__ = 'hr_profiles'

    hr_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    full_name = Column(String(100), nullable=False)
    position = Column(String(100))
    contact_phone = Column(String(20))
    company_name = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship("User", back_populates="hr_profile")
    vacancies = relationship("Vacancy", back_populates="hr")
    interviews_stage1 = relationship("InterviewStage1", back_populates="hr")
    interviews_stage2 = relationship("InterviewStage2", back_populates="hr")
    reports = relationship("CandidateReport", back_populates="hr")

    def __repr__(self) -> str:
        return f"<HRProfile(id={self.hr_id}, name='{self.full_name}')>"


class Resume(Base):
    """
    Резюме кандидата.
    Связано с пользователем с ролью Кандидат.
    """
    __tablename__ = 'resumes'

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    birth_date = Column(Date)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    education = Column(Text)
    work_experience = Column(Text)
    skills = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship("User", back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume(id={self.resume_id}, user_id={self.user_id})>"


class Vacancy(Base):
    """
    Вакансия, созданная HR-менеджером.
    """
    __tablename__ = 'vacancies'

    vacancy_id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    position_title = Column(String(100), nullable=False)
    job_description = Column(Text)
    requirements = Column(Text)
    status = Column(SQLEnum(VacancyStatus), default=VacancyStatus.OPEN)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr = relationship("HRProfile", back_populates="vacancies")
    interviews_stage1 = relationship("InterviewStage1", back_populates="vacancy")
    interviews_stage2 = relationship("InterviewStage2", back_populates="vacancy")
    reports = relationship("CandidateReport", back_populates="vacancy")

    def __repr__(self) -> str:
        return f"<Vacancy(id={self.vacancy_id}, title='{self.position_title}', status='{self.status.value}')>"


class InterviewStage1(Base):
    """
    Первый этап собеседования (оценка soft skills).
    """
    __tablename__ = 'interview_stage1'

    interview1_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview_date = Column(DateTime, nullable=False)
    questions = Column(Text)
    candidate_answers = Column(Text)
    soft_skills_score = Column(Integer)  # 0-100
    confidence_score = Column(Integer)  # 0-100
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", back_populates="interviews_stage1")
    hr = relationship("HRProfile", back_populates="interviews_stage1")
    vacancy = relationship("Vacancy", back_populates="interviews_stage1")
    stage2 = relationship("InterviewStage2", back_populates="stage1", uselist=False)
    reports = relationship("CandidateReport", back_populates="interview1")

    def __repr__(self) -> str:
        return f"<InterviewStage1(id={self.interview1_id}, candidate_id={self.user_id}, soft_score={self.soft_skills_score})>"


class InterviewStage2(Base):
    """
    Второй этап собеседования (технические навыки).
    """
    __tablename__ = 'interview_stage2'

    interview2_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview_date = Column(DateTime, nullable=False)
    technical_tasks = Column(Text)
    candidate_solutions = Column(Text)
    video_recording_path = Column(String(255))
    hard_skills_score = Column(Integer)  # 0-100
    final_result = Column(String(50))  # "Принят", "Отклонен", "На рассмотрении"
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", back_populates="interviews_stage2")
    hr = relationship("HRProfile", back_populates="interviews_stage2")
    stage1 = relationship("InterviewStage1", back_populates="stage2")
    vacancy = relationship("Vacancy", back_populates="interviews_stage2")
    reports = relationship("CandidateReport", back_populates="interview2")

    def __repr__(self) -> str:
        return f"<InterviewStage2(id={self.interview2_id}, hard_score={self.hard_skills_score}, result='{self.final_result}')>"


class CandidateReport(Base):
    """
    Итоговый отчет по кандидату после прохождения собеседований.
    """
    __tablename__ = 'candidate_reports'

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'))
    interview2_id = Column(Integer, ForeignKey('interview_stage2.interview2_id'))
    generation_date = Column(DateTime, default=datetime.utcnow)
    final_score = Column(Float)  # Общая оценка 0-100
    hr_recommendations = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("User", back_populates="reports")
    hr = relationship("HRProfile", back_populates="reports")
    vacancy = relationship("Vacancy", back_populates="reports")
    interview1 = relationship("InterviewStage1", back_populates="reports")
    interview2 = relationship("InterviewStage2", back_populates="reports")

    def __repr__(self) -> str:
        return f"<CandidateReport(id={self.report_id}, candidate_id={self.user_id}, score={self.final_score})>"


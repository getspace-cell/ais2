# ============================================================================
# ФАЙЛ: models/dao.py
# Описание: Объектно-реляционное отображение таблиц БД (ПРАВИЛЬНАЯ АРХИТЕКТУРА)
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
# КАНДИДАТЫ
# ============================================================================

class UserProfile(Base):
    """
    Профиль кандидата, проходящего собеседование.
    Базовая информация для входа в систему.
    """
    __tablename__ = 'user_profiles'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)

    # Отношения
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    interviews_stage1 = relationship("InterviewStage1", back_populates="candidate", cascade="all, delete-orphan")
    interviews_stage2 = relationship("InterviewStage2", back_populates="candidate", cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.user_id}, login='{self.login}')>"


class Resume(Base):
    """
    Резюме кандидата.
    Связано один-к-одному с UserProfile.
    """
    __tablename__ = 'resumes'

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), unique=True, nullable=False)
    
    # Личные данные
    full_name = Column(String(100), nullable=False)
    birth_date = Column(Date)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Профессиональная информация
    education = Column(Text)
    work_experience = Column(Text)
    skills = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    user = relationship("UserProfile", back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume(id={self.resume_id}, user_id={self.user_id}, name='{self.full_name}')>"


# ============================================================================
# HR МЕНЕДЖЕРЫ
# ============================================================================

class HRProfile(Base):
    """
    Профиль HR-менеджера.
    Базовая информация для входа в систему.
    """
    __tablename__ = 'hr_profiles'

    hr_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)

    # Отношения
    additional_info = relationship("HRAdditionalInfo", back_populates="hr", uselist=False, cascade="all, delete-orphan")
    vacancies = relationship("Vacancy", back_populates="hr", cascade="all, delete-orphan")
    interviews_stage1 = relationship("InterviewStage1", back_populates="hr", cascade="all, delete-orphan")
    interviews_stage2 = relationship("InterviewStage2", back_populates="hr", cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="hr", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<HRProfile(id={self.hr_id}, login='{self.login}')>"


class HRAdditionalInfo(Base):
    """
    Дополнительная информация об HR.
    Используется для статистики и контактов.
    Связана один-к-одному с HRProfile.
    """
    __tablename__ = 'hr_additional_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), unique=True, nullable=False)
    
    full_name = Column(String(100), nullable=False)
    position = Column(String(100))
    contact_phone = Column(String(20))
    company_name = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr = relationship("HRProfile", back_populates="additional_info")

    def __repr__(self) -> str:
        return f"<HRAdditionalInfo(hr_id={self.hr_id}, name='{self.full_name}')>"


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
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    
    position_title = Column(String(100), nullable=False)
    job_description = Column(Text)
    requirements = Column(Text)
    questions = Column(Text, comment="Вопросы для собеседования")
    status = Column(SQLEnum(VacancyStatus), default=VacancyStatus.OPEN)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr = relationship("HRProfile", back_populates="vacancies")
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
    Включает видеозапись и оценку.
    """
    __tablename__ = 'interview_stage1'

    interview1_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=False)
    questions = Column(Text, comment="Вопросы заданные на собеседовании")
    candidate_answers = Column(Text, comment="Ответы кандидата")
    video_recording_path = Column(String(255), comment="Путь к видеозаписи")
    soft_skills_score = Column(Integer, comment="Оценка soft skills 0-100")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("UserProfile", back_populates="interviews_stage1")
    hr = relationship("HRProfile", back_populates="interviews_stage1")
    vacancy = relationship("Vacancy", back_populates="interviews_stage1")
    stage2 = relationship("InterviewStage2", back_populates="stage1", uselist=False, cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="interview1")

    def __repr__(self) -> str:
        return f"<InterviewStage1(id={self.interview1_id}, candidate_id={self.user_id}, score={self.soft_skills_score})>"


class InterviewStage2(Base):
    """
    Второй этап собеседования - техническая оценка (hard skills).
    Включает видеозапись и технические задания.
    """
    __tablename__ = 'interview_stage2'

    interview2_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=False)
    technical_tasks = Column(Text, comment="Технические задания")
    candidate_solutions = Column(Text, comment="Решения кандидата")
    video_recording_path = Column(String(255), comment="Путь к видеозаписи")
    hard_skills_score = Column(Integer, comment="Оценка hard skills 0-100")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("UserProfile", back_populates="interviews_stage2")
    hr = relationship("HRProfile", back_populates="interviews_stage2")
    stage1 = relationship("InterviewStage1", back_populates="stage2")
    vacancy = relationship("Vacancy", back_populates="interviews_stage2")
    reports = relationship("CandidateReport", back_populates="interview2")

    def __repr__(self) -> str:
        return f"<InterviewStage2(id={self.interview2_id}, candidate_id={self.user_id}, score={self.hard_skills_score})>"


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
    user_id = Column(Integer, ForeignKey('user_profiles.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('hr_profiles.hr_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'))
    interview2_id = Column(Integer, ForeignKey('interview_stage2.interview2_id'))
    
    generation_date = Column(DateTime, default=datetime.utcnow)
    final_score = Column(Float, comment="Итоговая оценка 0-100")
    hr_recommendations = Column(Text, comment="Рекомендации HR")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    candidate = relationship("UserProfile", back_populates="reports")
    hr = relationship("HRProfile", back_populates="reports")
    vacancy = relationship("Vacancy", back_populates="reports")
    interview1 = relationship("InterviewStage1", back_populates="reports")
    interview2 = relationship("InterviewStage2", back_populates="reports")

    def __repr__(self) -> str:
        return f"<CandidateReport(id={self.report_id}, candidate_id={self.user_id}, score={self.final_score})>"


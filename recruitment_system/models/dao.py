# ============================================================================
# ФАЙЛ: models/dao.py (ИСПРАВЛЕННЫЙ)
# Описание: Объектно-реляционное отображение с детерминированными оценками
# ============================================================================

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    Float, ForeignKey, Enum as SQLEnum, JSON, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

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
# ЕДИНАЯ ТАБЛИЦА ПОЛЬЗОВАТЕЛЕЙ
# ============================================================================

class User(Base):
    """
    Единая таблица пользователей для авторизации.
    """
    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True, autoincrement=True)
    login = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(100), nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    registration_date = Column(DateTime, default=datetime.utcnow)
    
    # Связь с HR, который загрузил кандидата
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=True, comment="HR который загрузил резюме")
    
    # Отношения
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    hr_company_info = relationship("HRCompanyInfo", back_populates="hr", uselist=False, cascade="all, delete-orphan")
    
    # Связь HR с управляемыми кандидатами
    hr = relationship("User", remote_side=[user_id], foreign_keys=[hr_id], backref="managed_candidates")
    
    # Вакансии
    vacancies = relationship("Vacancy", back_populates="hr", cascade="all, delete-orphan")
    
    # Соответствия вакансиям
    vacancy_matches = relationship("VacancyMatch", back_populates="candidate", cascade="all, delete-orphan")
    
    # Интервью
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
    
    # Отчеты
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
# ИНФОРМАЦИЯ О КОМПАНИИ HR
# ============================================================================

class HRCompanyInfo(Base):
    """Дополнительная информация о HR и его компании."""
    __tablename__ = 'hr_company_info'

    info_id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    
    position = Column(String(100), comment="Должность HR в компании")
    department = Column(String(100), comment="Отдел")
    company_name = Column(String(200), nullable=False, comment="Название компании")
    company_description = Column(Text, comment="Описание компании")
    company_website = Column(String(200), comment="Веб-сайт компании")
    company_size = Column(Integer, comment="Количество сотрудников")
    industry = Column(String(100), comment="Отрасль")
    office_address = Column(Text, comment="Адрес офиса")
    contact_phone = Column(String(20), comment="Контактный телефон")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    hr = relationship("User", back_populates="hr_company_info")

    def __repr__(self) -> str:
        return f"<HRCompanyInfo(id={self.info_id}, hr_id={self.hr_id}, company='{self.company_name}')>"


# ============================================================================
# РЕЗЮМЕ (РАСШИРЕННОЕ)
# ============================================================================

class Resume(Base):
    """
    Резюме кандидата с расширенной информацией для анализа.
    """
    __tablename__ = 'resumes'

    resume_id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.user_id'), unique=True, nullable=False)
    
    # Личные данные
    birth_date = Column(Date)
    contact_phone = Column(String(20))
    contact_email = Column(String(100))
    
    # Профессиональная информация (базовая)
    education = Column(Text)
    work_experience = Column(Text)
    skills = Column(Text)
    
    # РАСШИРЕННАЯ информация для анализа
    technical_skills = Column(JSON, comment="Список технических навыков")
    soft_skills = Column(JSON, comment="Список soft skills")
    languages = Column(JSON, comment="Языки и уровень владения")
    certifications = Column(JSON, comment="Сертификаты и курсы")
    projects = Column(JSON, comment="Описание проектов")
    desired_position = Column(String(200), comment="Желаемая позиция")
    desired_salary = Column(Integer, comment="Желаемая зарплата")
    experience_years = Column(Integer, comment="Годы опыта")
    
    # AI анализ резюме (для справки)
    ai_summary = Column(Text, comment="Краткая сводка от AI")
    ai_strengths = Column(JSON, comment="Сильные стороны по мнению AI")
    ai_weaknesses = Column(JSON, comment="Слабые стороны по мнению AI")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume(id={self.resume_id}, user_id={self.user_id})>"


# ============================================================================
# ВАКАНСИИ (С КРИТЕРИЯМИ)
# ============================================================================

class Vacancy(Base):
    """
    Вакансия с детерминированными критериями отбора.
    """
    __tablename__ = 'vacancies'

    vacancy_id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Базовая информация
    position_title = Column(String(100), nullable=False)
    job_description = Column(Text)
    requirements = Column(Text)
    questions = Column(JSON, nullable=True, comment="Список вопросов для собеседования")
    status = Column(SQLEnum(VacancyStatus), default=VacancyStatus.OPEN)
    
    # КРИТЕРИИ ОТБОРА
    min_experience_years = Column(Integer, default=0, comment="Минимальный опыт (лет)")
    max_experience_years = Column(Integer, nullable=True, comment="Максимальный опыт (лет)")
    min_age = Column(Integer, nullable=True, comment="Минимальный возраст")
    max_age = Column(Integer, nullable=True, comment="Максимальный возраст")
    education_required = Column(Integer, default=0, comment="Требуется ли высшее образование (0/1)")
    education_level = Column(String(50), nullable=True, comment="Уровень: Бакалавр/Магистр/Специалист")
    
    required_technical_skills = Column(JSON, comment="Обязательные технические навыки")
    optional_technical_skills = Column(JSON, comment="Желательные технические навыки")
    required_soft_skills = Column(JSON, comment="Обязательные soft skills")
    required_languages = Column(JSON, comment='[{"language": "...", "min_level": "B2"}]')
    
    min_salary = Column(Integer, nullable=True, comment="Минимальная зарплата")
    max_salary = Column(Integer, nullable=True, comment="Максимальная зарплата")
    
    # Веса для расчета скора
    weight_experience = Column(Integer, default=30, comment="Вес опыта в скоре %")
    weight_technical_skills = Column(Integer, default=40, comment="Вес технических навыков %")
    weight_soft_skills = Column(Integer, default=20, comment="Вес soft skills %")
    weight_languages = Column(Integer, default=10, comment="Вес языков %")
    
    created_at = Column(DateTime, default=datetime.utcnow)

    # Отношения
    hr = relationship("User", back_populates="vacancies")
    matches = relationship("VacancyMatch", back_populates="vacancy", cascade="all, delete-orphan")
    
    # ИСПРАВЛЕНО: используем правильные имена relationships
    interviews_as_vacancy = relationship("InterviewStage1", back_populates="vacancy", cascade="all, delete-orphan")
    interviews_stage2 = relationship("InterviewStage2", back_populates="vacancy", cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="vacancy", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vacancy(id={self.vacancy_id}, title='{self.position_title}', status='{self.status.value}')>"


# ============================================================================
# СООТВЕТСТВИЕ КАНДИДАТОВ ВАКАНСИЯМ
# ============================================================================

class VacancyMatch(Base):
    """
    Детерминированная оценка соответствия кандидата вакансии.
    """
    __tablename__ = 'vacancy_matches'
    __table_args__ = (
        UniqueConstraint('vacancy_id', 'candidate_id', name='unique_vacancy_candidate'),
    )

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Оценки соответствия (0-100)
    overall_score = Column(Integer, nullable=False, comment="Общая оценка 0-100")
    experience_score = Column(Integer, comment="Оценка опыта 0-100")
    technical_skills_score = Column(Integer, comment="Оценка технических навыков 0-100")
    soft_skills_score = Column(Integer, comment="Оценка soft skills 0-100")
    language_score = Column(Integer, comment="Оценка языков 0-100")
    education_score = Column(Integer, comment="Соответствие образованию 0-100")
    age_score = Column(Integer, comment="Соответствие возрасту 0-100")
    
    # Детали совпадений
    matched_technical_skills = Column(JSON, comment="Совпавшие технические навыки")
    missing_technical_skills = Column(JSON, comment="Отсутствующие технические навыки")
    matched_soft_skills = Column(JSON, comment="Совпавшие soft skills")
    matched_languages = Column(JSON, comment="Совпавшие языки")
    
    # AI-анализ (для справки HR)
    ai_summary = Column(Text, comment="Краткая сводка от AI (из резюме)")
    ai_strengths = Column(JSON, comment="Сильные стороны (из резюме)")
    ai_weaknesses = Column(JSON, comment="Слабые стороны (из резюме)")
    
    # Статус
    is_invited = Column(Integer, default=0, comment="Приглашен на интервью (0/1)")
    is_rejected = Column(Integer, default=0, comment="Отклонен HR (0/1)")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy = relationship("Vacancy", back_populates="matches")
    candidate = relationship("User", back_populates="vacancy_matches")

    def __repr__(self) -> str:
        return f"<VacancyMatch(vacancy_id={self.vacancy_id}, candidate_id={self.candidate_id}, score={self.overall_score})>"


# ============================================================================
# СОБЕСЕДОВАНИЯ
# ============================================================================

class InterviewStage1(Base):
    """Первый этап собеседования - оценка soft skills."""
    __tablename__ = 'interview_stage1'

    interview1_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=True)
    questions = Column(Text, nullable=True)
    candidate_answers = Column(Text, nullable=True)
    video_path = Column(String(500), nullable=True)
    audio_path = Column(String(500), nullable=True)
    soft_skills_score = Column(Integer, nullable=True)
    confidence_score = Column(Integer, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="interviews_stage1_as_candidate")
    hr = relationship("User", foreign_keys=[hr_id], back_populates="interviews_stage1_as_hr")
    vacancy = relationship("Vacancy", back_populates="interviews_as_vacancy")
    stage2 = relationship("InterviewStage2", back_populates="stage1", uselist=False, cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="interview1")

    def __repr__(self) -> str:
        return f"<InterviewStage1(id={self.interview1_id}, candidate_id={self.candidate_id})>"


class InterviewStage2(Base):
    """Второй этап собеседования - техническая оценка."""
    __tablename__ = 'interview_stage2'

    interview2_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    
    interview_date = Column(DateTime, nullable=False)
    technical_tasks = Column(Text)
    candidate_solutions = Column(Text)
    hard_skills_score = Column(Integer)
    
    created_at = Column(DateTime, default=datetime.utcnow)

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
    """Итоговый отчет по кандидату."""
    __tablename__ = 'candidate_reports'

    report_id = Column(Integer, primary_key=True, autoincrement=True)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    interview1_id = Column(Integer, ForeignKey('interview_stage1.interview1_id'))
    interview2_id = Column(Integer, ForeignKey('interview_stage2.interview2_id'))
    
    generation_date = Column(DateTime, default=datetime.utcnow)
    final_score = Column(Float)
    hr_recommendations = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    candidate = relationship("User", foreign_keys=[candidate_id], back_populates="reports_as_candidate")
    hr = relationship("User", foreign_keys=[hr_id], back_populates="reports_as_hr")
    vacancy = relationship("Vacancy", back_populates="reports")
    interview1 = relationship("InterviewStage1", back_populates="reports")
    interview2 = relationship("InterviewStage2", back_populates="reports")

    def __repr__(self) -> str:
        return f"<CandidateReport(id={self.report_id}, candidate_id={self.candidate_id}, score={self.final_score})>"
# ============================================================================
# ФАЙЛ: models/dao.py (ОБНОВЛЕННЫЙ)
# Описание: Объектно-реляционное отображение с оценками пригодности
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
    
    # Отношения
    resume = relationship("Resume", back_populates="user", uselist=False, cascade="all, delete-orphan")
    hr_company_info = relationship("HRCompanyInfo", back_populates="hr", uselist=False, cascade="all, delete-orphan")
    
    # Новое: связь с HR, который загрузил кандидата
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=True, comment="HR который загрузил резюме")
    hr = relationship("User", remote_side=[user_id], foreign_keys=[hr_id], backref="managed_candidates")
    
    vacancies = relationship("Vacancy", back_populates="hr", cascade="all, delete-orphan")
    vacancy_matches = relationship("VacancyMatch", back_populates="candidate", cascade="all, delete-orphan")
    
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
    Резюме кандидата с расширенной информацией для AI анализа.
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
    
    # НОВОЕ: Расширенная информация для анализа
    technical_skills = Column(JSON, comment="Список технических навыков")
    soft_skills = Column(JSON, comment="Список soft skills")
    languages = Column(JSON, comment="Языки и уровень владения")
    certifications = Column(JSON, comment="Сертификаты и курсы")
    projects = Column(JSON, comment="Описание проектов")
    desired_position = Column(String(200), comment="Желаемая позиция")
    desired_salary = Column(Integer, comment="Желаемая зарплата")
    experience_years = Column(Integer, comment="Годы опыта")
    
    # AI анализ резюме
    ai_summary = Column(Text, comment="Краткая сводка от AI")
    ai_strengths = Column(JSON, comment="Сильные стороны по мнению AI")
    ai_weaknesses = Column(JSON, comment="Слабые стороны по мнению AI")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="resume")

    def __repr__(self) -> str:
        return f"<Resume(id={self.resume_id}, user_id={self.user_id})>"


# ============================================================================
# ВАКАНСИИ (РАСШИРЕННЫЕ)
# ============================================================================

class Vacancy(Base):
    """
    Вакансия с требованиями для AI анализа пригодности кандидатов.
    """
    __tablename__ = 'vacancies'

    vacancy_id = Column(Integer, primary_key=True, autoincrement=True)
    hr_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    position_title = Column(String(100), nullable=False)
    job_description = Column(Text)
    requirements = Column(Text)
    
    # НОВОЕ: Структурированные требования для AI
    required_technical_skills = Column(JSON, comment="Обязательные технические навыки")
    optional_technical_skills = Column(JSON, comment="Желательные технические навыки")
    required_soft_skills = Column(JSON, comment="Обязательные soft skills")
    required_experience_years = Column(Integer, comment="Минимальный опыт работы")
    required_languages = Column(JSON, comment="Требуемые языки")
    salary_range = Column(JSON, comment="Вилка зарплаты {min, max}")
    
    questions = Column(JSON, nullable=True, comment="Список вопросов для собеседования")
    status = Column(SQLEnum(VacancyStatus), default=VacancyStatus.OPEN)
    
    created_at = Column(DateTime, default=datetime.utcnow)

    hr = relationship("User", back_populates="vacancies")
    matches = relationship("VacancyMatch", back_populates="vacancy", cascade="all, delete-orphan")
    interviews_stage1 = relationship("InterviewStage1", back_populates="vacancy", cascade="all, delete-orphan")
    interviews_stage2 = relationship("InterviewStage2", back_populates="vacancy", cascade="all, delete-orphan")
    reports = relationship("CandidateReport", back_populates="vacancy", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Vacancy(id={self.vacancy_id}, title='{self.position_title}', status='{self.status.value}')>"


# ============================================================================
# НОВАЯ ТАБЛИЦА: СООТВЕТСТВИЕ КАНДИДАТОВ ВАКАНСИЯМ
# ============================================================================

class VacancyMatch(Base):
    """
    Оценка соответствия кандидата вакансии.
    Автоматически создается при создании вакансии для всех кандидатов HR.
    """
    __tablename__ = 'vacancy_matches'
    __table_args__ = (
        UniqueConstraint('vacancy_id', 'candidate_id', name='unique_vacancy_candidate'),
    )

    match_id = Column(Integer, primary_key=True, autoincrement=True)
    vacancy_id = Column(Integer, ForeignKey('vacancies.vacancy_id'), nullable=False)
    candidate_id = Column(Integer, ForeignKey('users.user_id'), nullable=False)
    
    # Оценки соответствия (0-100)
    overall_score = Column(Float, nullable=False, comment="Общая оценка пригодности 0-100")
    technical_match_score = Column(Float, comment="Соответствие технических навыков")
    experience_match_score = Column(Float, comment="Соответствие опыта")
    soft_skills_match_score = Column(Float, comment="Соответствие soft skills")
    
    # Детальный анализ
    matched_skills = Column(JSON, comment="Совпадающие навыки")
    missing_skills = Column(JSON, comment="Недостающие навыки")
    ai_recommendation = Column(Text, comment="Рекомендация AI")
    ai_pros = Column(JSON, comment="Преимущества кандидата")
    ai_cons = Column(JSON, comment="Недостатки кандидата")
    
    # Статус отбора
    is_invited = Column(Integer, default=0, comment="Приглашен ли на интервью (0/1)")
    is_rejected = Column(Integer, default=0, comment="Отклонен ли HR (0/1)")
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    vacancy = relationship("Vacancy", back_populates="matches")
    candidate = relationship("User", back_populates="vacancy_matches")

    def __repr__(self) -> str:
        return f"<VacancyMatch(vacancy_id={self.vacancy_id}, candidate_id={self.candidate_id}, score={self.overall_score})>"


# ============================================================================
# СОБЕСЕДОВАНИЯ (БЕЗ ИЗМЕНЕНИЙ)
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
    vacancy = relationship("Vacancy", back_populates="interviews_stage1")
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
# ОТЧЕТЫ (БЕЗ ИЗМЕНЕНИЙ)
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
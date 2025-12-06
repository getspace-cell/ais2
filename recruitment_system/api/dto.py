from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, date
from enum import Enum


# Enum классы
class UserRoleDTO(str, Enum):
    HR = "HR"
    CANDIDATE = "Кандидат"


class VacancyStatusDTO(str, Enum):
    OPEN = "Открыта"
    CLOSED = "Закрыта"
    ON_HOLD = "На паузе"


# ========== Auth DTO ==========

class UserRegisterDTO(BaseModel):
    """DTO для регистрации пользователя"""
    login: str = Field(..., min_length=3, max_length=50, description="Логин пользователя")
    password: str = Field(..., min_length=6, description="Пароль (минимум 6 символов)")
    email: EmailStr = Field(..., description="Email адрес")
    full_name: str = Field(..., min_length=2, max_length=100, description="Полное имя")
    role: UserRoleDTO = Field(..., description="Роль: HR или Кандидат")
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "ivan_petrov",
                "password": "securepass123",
                "email": "ivan@example.com",
                "full_name": "Иван Петров",
                "role": "Кандидат"
            }
        }


class UserLoginDTO(BaseModel):
    """DTO для входа в систему"""
    login: str = Field(..., description="Логин")
    password: str = Field(..., description="Пароль")
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "ivan_petrov",
                "password": "securepass123"
            }
        }


class TokenDTO(BaseModel):
    """DTO для ответа с токеном"""
    access_token: str = Field(..., description="JWT токен доступа")
    token_type: str = Field(default="bearer", description="Тип токена")
    user_id: int = Field(..., description="ID пользователя")
    role: str = Field(..., description="Роль пользователя")
    full_name: str = Field(..., description="Полное имя")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user_id": 1,
                "role": "Кандидат",
                "full_name": "Иван Петров"
            }
        }


# ========== User DTO ==========

class UserResponseDTO(BaseModel):
    """DTO для ответа с информацией о пользователе"""
    user_id: int
    login: str
    email: str
    full_name: str
    role: str
    registration_date: datetime
    
    class Config:
        from_attributes = True


class UserProfileDTO(BaseModel):
    """DTO для профиля текущего пользователя"""
    user_id: int
    login: str
    email: str
    full_name: str
    role: str
    registration_date: datetime
    
    class Config:
        from_attributes = True

# ========== HR Company Info DTO ==========

class HRCompanyInfoCreateDTO(BaseModel):
    """DTO для создания информации о компании HR"""
    position: Optional[str] = Field(None, max_length=100, description="Должность HR")
    department: Optional[str] = Field(None, max_length=100, description="Отдел")
    company_name: str = Field(..., min_length=2, max_length=200, description="Название компании")
    company_description: Optional[str] = Field(None, description="Описание компании")
    company_website: Optional[str] = Field(None, max_length=200, description="Веб-сайт компании")
    company_size: Optional[int] = Field(None, ge=1, description="Количество сотрудников")
    industry: Optional[str] = Field(None, max_length=100, description="Отрасль")
    office_address: Optional[str] = Field(None, description="Адрес офиса")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Контактный телефон")
    
    class Config:
        json_schema_extra = {
            "example": {
                "position": "Senior HR Manager",
                "department": "Отдел по работе с персоналом",
                "company_name": "TechCorp Solutions",
                "company_description": "Инновационная IT-компания, специализирующаяся на разработке корпоративных решений",
                "company_website": "https://techcorp.com",
                "company_size": 250,
                "industry": "Информационные технологии",
                "office_address": "Москва, ул. Тверская, д. 1",
                "contact_phone": "+7-495-123-45-67"
            }
        }


class HRCompanyInfoUpdateDTO(BaseModel):
    """DTO для обновления информации о компании HR"""
    position: Optional[str] = Field(None, max_length=100)
    department: Optional[str] = Field(None, max_length=100)
    company_name: Optional[str] = Field(None, min_length=2, max_length=200)
    company_description: Optional[str] = None
    company_website: Optional[str] = Field(None, max_length=200)
    company_size: Optional[int] = Field(None, ge=1)
    industry: Optional[str] = Field(None, max_length=100)
    office_address: Optional[str] = None
    contact_phone: Optional[str] = Field(None, max_length=20)


class HRCompanyInfoResponseDTO(BaseModel):
    """DTO для ответа с информацией о компании HR"""
    info_id: int
    hr_id: int
    position: Optional[str]
    department: Optional[str]
    company_name: str
    company_description: Optional[str]
    company_website: Optional[str]
    company_size: Optional[int]
    industry: Optional[str]
    office_address: Optional[str]
    contact_phone: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "info_id": 1,
                "hr_id": 5,
                "position": "Senior HR Manager",
                "department": "Отдел по работе с персоналом",
                "company_name": "TechCorp Solutions",
                "company_description": "Инновационная IT-компания",
                "company_website": "https://techcorp.com",
                "company_size": 250,
                "industry": "Информационные технологии",
                "office_address": "Москва, ул. Тверская, д. 1",
                "contact_phone": "+7-495-123-45-67",
                "created_at": "2024-01-15T10:30:00",
                "updated_at": "2024-01-15T10:30:00"
            }
        }

# ========== Vacancy DTO ==========

class VacancyCreateDTO(BaseModel):
    """DTO для создания вакансии"""
    position_title: str = Field(..., min_length=2, max_length=100, description="Название должности")
    job_description: Optional[str] = Field(None, description="Описание работы")
    requirements: Optional[str] = Field(None, description="Требования к кандидату")
    
    class Config:
        json_schema_extra = {
            "example": {
                "position_title": "Python Developer",
                "job_description": "Разработка backend на FastAPI",
                "requirements": "Python 3.9+, FastAPI, PostgreSQL, опыт 3+ года"
            }
        }


class VacancyUpdateDTO(BaseModel):
    """DTO для обновления вакансии"""
    position_title: Optional[str] = Field(None, min_length=2, max_length=100)
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    status: Optional[VacancyStatusDTO] = None


class VacancyResponseDTO(BaseModel):
    """DTO для ответа с информацией о вакансии"""
    vacancy_id: int
    hr_id: int
    position_title: str
    job_description: Optional[str]
    requirements: Optional[str]
    questions: Optional[list]
    candidate_ids: Optional[list] = Field(None, description="Список ID прикрепленных кандидатов")
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ========== Resume DTO ==========

class ResumeCreateDTO(BaseModel):
    """DTO для создания резюме"""
    birth_date: Optional[date] = Field(None, description="Дата рождения")
    contact_phone: Optional[str] = Field(None, max_length=20, description="Контактный телефон")
    contact_email: Optional[EmailStr] = Field(None, description="Контактный email")
    education: Optional[str] = Field(None, description="Образование")
    work_experience: Optional[str] = Field(None, description="Опыт работы")
    skills: Optional[str] = Field(None, description="Навыки")
    
    class Config:
        json_schema_extra = {
            "example": {
                "birth_date": "1995-05-15",
                "contact_phone": "+7-900-123-45-67",
                "contact_email": "candidate@email.com",
                "education": "МГУ, Факультет ВМК, 2017",
                "work_experience": "5 лет Python разработки",
                "skills": "Python, FastAPI, Django, PostgreSQL"
            }
        }


class ResumeUpdateDTO(BaseModel):
    """DTO для обновления резюме"""
    birth_date: Optional[date] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    education: Optional[str] = None
    work_experience: Optional[str] = None
    skills: Optional[str] = None


class ResumeResponseDTO(BaseModel):
    """DTO для ответа с информацией о резюме"""
    resume_id: int
    user_id: int
    birth_date: Optional[date]
    contact_phone: Optional[str]
    contact_email: Optional[str]
    education: Optional[str]
    work_experience: Optional[str]
    skills: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Interview DTO ==========

class InterviewStage1CreateDTO(BaseModel):
    """DTO для создания первого этапа собеседования"""
    candidate_id: int = Field(..., description="ID кандидата")
    vacancy_id: int = Field(..., description="ID вакансии")
    interview_date: datetime = Field(..., description="Дата и время собеседования")
    questions: Optional[str] = Field(None, description="Вопросы")
    candidate_answers: Optional[str] = Field(None, description="Ответы кандидата")
    soft_skills_score: Optional[int] = Field(None, ge=0, le=100, description="Оценка soft skills")
    confidence_score: Optional[int] = Field(None, ge=0, le=100, description="Оценка уверенности")


class InterviewStage1ResponseDTO(BaseModel):
    """DTO для ответа с информацией о первом этапе"""
    interview1_id: int
    candidate_id: int
    hr_id: int
    vacancy_id: int
    interview_date: Optional[datetime]
    soft_skills_score: Optional[int]
    confidence_score: Optional[int]
    candidate_answers : Optional[str]
    video_path : Optional[str]
    audio_path: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterviewStage2CreateDTO(BaseModel):
    """DTO для создания второго этапа собеседования"""
    candidate_id: int = Field(..., description="ID кандидата")
    interview1_id: int = Field(..., description="ID первого этапа")
    vacancy_id: int = Field(..., description="ID вакансии")
    interview_date: datetime = Field(..., description="Дата и время собеседования")
    technical_tasks: Optional[str] = Field(None, description="Технические задания")
    candidate_solutions: Optional[str] = Field(None, description="Решения кандидата")
    hard_skills_score: Optional[int] = Field(None, ge=0, le=100, description="Оценка hard skills")


class InterviewStage2ResponseDTO(BaseModel):
    """DTO для ответа с информацией о втором этапе"""
    interview2_id: int
    candidate_id: int
    hr_id: int
    interview1_id: int
    vacancy_id: int
    interview_date: datetime
    hard_skills_score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Report DTO ==========

class ReportCreateDTO(BaseModel):
    """DTO для создания отчета"""
    candidate_id: int = Field(..., description="ID кандидата")
    vacancy_id: int = Field(..., description="ID вакансии")
    interview1_id: Optional[int] = Field(None, description="ID первого этапа")
    interview2_id: Optional[int] = Field(None, description="ID второго этапа")
    final_score: Optional[float] = Field(None, ge=0, le=100, description="Итоговая оценка")
    hr_recommendations: Optional[str] = Field(None, description="Рекомендации HR")


class ReportResponseDTO(BaseModel):
    """DTO для ответа с информацией об отчете"""
    report_id: int
    candidate_id: int
    hr_id: int
    vacancy_id: int
    interview1_id: Optional[int]
    interview2_id: Optional[int]
    generation_date: datetime
    final_score: Optional[float]
    hr_recommendations: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Message DTO ==========

class MessageDTO(BaseModel):
    """DTO для простых сообщений"""
    message: str
    detail: Optional[str] = None

from pydantic import BaseModel, Field
from typing import List, Optional

# ========== Resume Upload DTO ==========

class UploadResumesResponseDTO(BaseModel):
    """DTO для ответа после загрузки резюме"""
    message: str
    created_candidates: List[dict] = Field(..., description="Список созданных/найденных кандидатов")
    total_processed: int
    new_users: int = Field(..., description="Количество новых пользователей")
    existing_users: int = Field(..., description="Количество существующих пользователей")
    errors: int = Field(..., description="Количество ошибок")
    error_details: Optional[List[dict]] = Field(None, description="Детали ошибок")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Успешно обработано 5 резюме",
                "created_candidates": [
                    {
                        "user_id": 10,
                        "full_name": "Иван Иванов",
                        "email": "ivan@email.com",
                        "login": "candidate_10",
                        "password": "temp_pass_abc123",
                        "status": "new"
                    },
                    {
                        "user_id": 7,
                        "full_name": "Петр Петров",
                        "email": "petr@email.com",
                        "login": "existing_candidate",
                        "status": "existing"
                    }
                ],
                "total_processed": 5,
                "new_users": 4,
                "existing_users": 1,
                "errors": 0,
                "error_details": None
            }
        }


# ========== Interview Invitation DTO ==========

class InviteCandidatesDTO(BaseModel):
    """DTO для приглашения кандидатов на собеседование"""
    candidate_ids: List[int] = Field(..., description="Список ID кандидатов")
    vacancy_id: int = Field(..., description="ID вакансии")
    
    class Config:
        json_schema_extra = {
            "example": {
                "candidate_ids": [10, 11, 12],
                "vacancy_id": 1
            }
        }


class InvitationResponseDTO(BaseModel):
    """DTO для ответа после отправки приглашений"""
    message: str
    total_invited: int
    successful_invites: int
    failed_invites: int
    failed_emails: List[str]
    created_interviews: int = Field(..., description="Количество созданных записей интервью")
    interview_ids: List[int] = Field(..., description="ID созданных интервью")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Приглашения отправлены",
                "total_invited": 5,
                "successful_invites": 5,
                "failed_invites": 0,
                "failed_emails": [],
                "created_interviews": 5,
                "interview_ids": [1, 2, 3, 4, 5]
            }
        }



# ========== Interview Completion DTO ==========

class InterviewAnswersDTO(BaseModel):
    """DTO для отправки ответов на интервью"""
    vacancy_id: int = Field(..., description="ID вакансии")
    text_answers: str = Field(..., description="Текстовые ответы кандидата")
    # video_base64 будет передаваться через multipart/form-data
    
    class Config:
        json_schema_extra = {
            "example": {
                "vacancy_id": 1,
                "text_answers": "Ответ на вопрос 1: ...\nОтвет на вопрос 2: ..."
            }
        }


class InterviewResultDTO(BaseModel):
    """DTO для результата интервью"""
    interview1_id: int
    soft_skills_score: int
    confidence_score: int
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "interview1_id": 15,
                "soft_skills_score": 85,
                "confidence_score": 78,
                "message": "Интервью успешно завершено и оценено"
            }
        }


# ========== Vacancy with Questions DTO ==========

class VacancyWithQuestionsDTO(BaseModel):
    """DTO для вакансии с вопросами"""
    position_title: str
    job_description: Optional[str]
    requirements: Optional[str]
    questions: Optional[List[str]]
    
    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "position_title": "Python Developer",
                "job_description": "Разработка backend",
                "requirements": "Python 3.9+, FastAPI",
                "questions": [
                    "Какой стек вы планируете изучать?",
                    "Ваш коллега не вовремя закончил проект, ваши действия?"
                ],
            }
        }
        
class VacancyCandidatesStatsDTO(BaseModel):
    """DTO для статистики по кандидатам вакансии"""
    vacancy_id: int
    position_title: str
    total_candidates: int = Field(..., description="Всего кандидатов прикреплено")
    invited_candidates: int = Field(..., description="Приглашено на интервью")
    completed_interviews: int = Field(..., description="Завершили интервью")
    pending_interviews: int = Field(..., description="Ожидают прохождения интервью")
    not_invited_yet: int = Field(..., description="Еще не приглашены")
    
    class Config:
        json_schema_extra = {
            "example": {
                "vacancy_id": 1,
                "position_title": "Python Developer",
                "total_candidates": 10,
                "invited_candidates": 7,
                "completed_interviews": 5,
                "pending_interviews": 2,
                "not_invited_yet": 3
            }
        }

# ========== Vacancy Match DTO ==========

class VacancyMatchResponseDTO(BaseModel):
    """DTO для ответа с информацией о соответствии кандидата вакансии"""
    match_id: int
    vacancy_id: int
    candidate_id: int
    candidate_name: str = Field(..., description="Имя кандидата")
    
    overall_score: float = Field(..., description="Общая оценка пригодности 0-100")
    technical_match_score: Optional[float]
    experience_match_score: Optional[float]
    soft_skills_match_score: Optional[float]
    
    matched_skills: Optional[List[str]]
    missing_skills: Optional[List[str]]
    ai_recommendation: Optional[str]
    ai_pros: Optional[List[str]]
    ai_cons: Optional[List[str]]
    
    is_invited: int = Field(..., description="Приглашен на интервью (0/1)")
    is_rejected: int = Field(..., description="Отклонен HR (0/1)")
    
    created_at: datetime
    
    class Config:
        from_attributes = True


class VacancyMatchFilterDTO(BaseModel):
    """DTO для фильтрации кандидатов по вакансии"""
    min_overall_score: Optional[float] = Field(None, ge=0, le=100, description="Минимальная общая оценка")
    min_technical_score: Optional[float] = Field(None, ge=0, le=100)
    min_experience_score: Optional[float] = Field(None, ge=0, le=100)
    required_skills: Optional[List[str]] = Field(None, description="Обязательные навыки")
    hide_rejected: bool = Field(True, description="Скрыть отклоненных кандидатов")
    hide_invited: bool = Field(False, description="Скрыть уже приглашенных")
    sort_by: str = Field("overall_score", description="Поле для сортировки")
    sort_desc: bool = Field(True, description="Сортировка по убыванию")
    
    class Config:
        json_schema_extra = {
            "example": {
                "min_overall_score": 70.0,
                "min_technical_score": 60.0,
                "required_skills": ["Python", "FastAPI"],
                "hide_rejected": True,
                "hide_invited": False,
                "sort_by": "overall_score",
                "sort_desc": True
            }
        }


class RejectCandidateDTO(BaseModel):
    """DTO для отклонения кандидата"""
    candidate_id: int = Field(..., description="ID кандидата")
    reason: Optional[str] = Field(None, description="Причина отклонения")


# ========== Extended Vacancy DTO ==========

class VacancyCreateExtendedDTO(BaseModel):
    """DTO для создания вакансии с автоматическим анализом"""
    position_title: str = Field(..., min_length=2, max_length=100)
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    questions: Optional[List[str]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "position_title": "Senior Backend Developer",
                "job_description": "Разработка высоконагруженных систем на Python/FastAPI",
                "requirements": "Python 3.9+, FastAPI, PostgreSQL, Docker, опыт 5+ лет, английский B2",
                "questions": [
                    "Расскажите о вашем опыте работы с микросервисами",
                    "Как вы подходите к оптимизации производительности?"
                ]
            }
        }


class VacancyWithMatchesResponseDTO(BaseModel):
    """DTO для вакансии со списком подходящих кандидатов"""
    vacancy_id: int
    position_title: str
    job_description: Optional[str]
    requirements: Optional[str]
    status: str
    
    total_candidates: int = Field(..., description="Всего кандидатов в базе HR")
    matched_candidates: int = Field(..., description="Кандидатов после фильтрации")
    average_match_score: float = Field(..., description="Средняя оценка соответствия")
    
    top_candidates: List[VacancyMatchResponseDTO] = Field(..., description="Топ кандидаты")
    
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "vacancy_id": 1,
                "position_title": "Senior Backend Developer",
                "job_description": "...",
                "requirements": "...",
                "status": "Открыта",
                "total_candidates": 50,
                "matched_candidates": 15,
                "average_match_score": 72.5,
                "top_candidates": [],
                "created_at": "2024-01-15T10:00:00"
            }
        }


# ========== Bulk Upload Response (Updated) ==========

class BulkUploadResponseDTO(BaseModel):
    """DTO для ответа после массовой загрузки резюме"""
    message: str
    total_processed: int
    successful: int
    failed: int
    candidates: List[dict] = Field(..., description="Список созданных кандидатов")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Успешно обработано 10 резюме",
                "total_processed": 10,
                "successful": 9,
                "failed": 1,
                "candidates": [
                    {
                        "user_id": 15,
                        "full_name": "Иван Иванов",
                        "email": "ivan@email.com",
                        "desired_position": "Backend Developer",
                        "experience_years": 5
                    }
                ]
            }
        }
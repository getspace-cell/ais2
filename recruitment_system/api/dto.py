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
    interview_date: datetime
    soft_skills_score: Optional[int]
    confidence_score: Optional[int]
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
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


# ========== User DTO ==========

class UserCreateDTO(BaseModel):
    login: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    role: UserRoleDTO
    
    class Config:
        json_schema_extra = {
            "example": {
                "login": "hr_test",
                "password": "password123",
                "email": "hr@company.com",
                "full_name": "Тестовый HR",
                "role": "HR"
            }
        }


class UserResponseDTO(BaseModel):
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
    position_title: str = Field(..., min_length=2, max_length=100)
    job_description: Optional[str] = None
    requirements: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "position_title": "Python Developer",
                "job_description": "Разработка backend на FastAPI",
                "requirements": "Python 3.9+, FastAPI, PostgreSQL"
            }
        }


class VacancyResponseDTO(BaseModel):
    vacancy_id: int
    hr_id: int
    position_title: str
    job_description: Optional[str]
    requirements: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Resume DTO ==========

class ResumeCreateDTO(BaseModel):
    birth_date: Optional[date] = None
    contact_phone: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    education: Optional[str] = None
    work_experience: Optional[str] = None
    skills: Optional[str] = None


class ResumeResponseDTO(BaseModel):
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
    user_id: int
    vacancy_id: int
    interview_date: datetime
    questions: Optional[str] = None
    candidate_answers: Optional[str] = None
    soft_skills_score: Optional[int] = Field(None, ge=0, le=100)
    confidence_score: Optional[int] = Field(None, ge=0, le=100)


class InterviewStage1ResponseDTO(BaseModel):
    interview1_id: int
    user_id: int
    hr_id: int
    vacancy_id: int
    interview_date: datetime
    soft_skills_score: Optional[int]
    confidence_score: Optional[int]
    created_at: datetime
    
    class Config:
        from_attributes = True


# ========== Message DTO ==========

class MessageDTO(BaseModel):
    message: str
    detail: Optional[str] = None
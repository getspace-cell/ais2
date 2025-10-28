from fastapi import APIRouter, HTTPException, status, Depends
from typing import List
from datetime import datetime
import hashlib

from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import (
    User, UserRole, HRProfile, Resume, Vacancy,
    VacancyStatus, InterviewStage1, InterviewStage2,
    CandidateReport
)
from api.dto import *

# Инициализация
DATABASE_URL = 'sqlite:///recruitment.db'
db_repo = DatabaseRepository(DATABASE_URL)
db_repo.create_tables()

def get_service():
    return RecruitmentService(db_repo)

# Роутер
router = APIRouter(prefix='/api/v1', tags=['Simple HR API'])


# ========== USERS ==========

@router.post('/users',
             response_model=UserResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание пользователя")
async def create_user(
    user_data: UserCreateDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Создание нового пользователя (HR или кандидат)"""
    try:
        # Хешируем пароль
        password_hash = hashlib.sha256(user_data.password.encode()).hexdigest()
        
        # Конвертируем роль
        role = UserRole.HR if user_data.role == UserRoleDTO.HR else UserRole.CANDIDATE
        
        user = service.create_user(
            login=user_data.login,
            password_hash=password_hash,
            email=user_data.email,
            full_name=user_data.full_name,
            role=role
        )
        return UserResponseDTO.from_orm(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/users',
            response_model=List[UserResponseDTO],
            summary="Получение всех пользователей")
async def get_all_users(
    role: Optional[UserRoleDTO] = None,
    service: RecruitmentService = Depends(get_service)
):
    """Получение списка всех пользователей с фильтрацией по роли"""
    user_role = None
    if role:
        user_role = UserRole.HR if role == UserRoleDTO.HR else UserRole.CANDIDATE
    
    users = service.get_all_users(role=user_role)
    return [UserResponseDTO.from_orm(u) for u in users]


@router.get('/users/{user_id}',
            response_model=UserResponseDTO,
            summary="Получение пользователя по ID")
async def get_user(
    user_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Получение информации о конкретном пользователе"""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return UserResponseDTO.from_orm(user)


@router.delete('/users/{user_id}',
               response_model=MessageDTO,
               summary="Удаление пользователя")
async def delete_user(
    user_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Удаление пользователя из системы"""
    result = service.delete_user(user_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return MessageDTO(message="Пользователь успешно удален")


# ========== VACANCIES ==========

@router.post('/vacancies',
             response_model=VacancyResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание вакансии")
async def create_vacancy(
    vacancy_data: VacancyCreateDTO,
    hr_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """
    Создание новой вакансии.
    
    hr_id передается как query parameter
    """
    try:
        vacancy = service.create_vacancy(
            hr_id=hr_id,
            position_title=vacancy_data.position_title,
            job_description=vacancy_data.job_description,
            requirements=vacancy_data.requirements,
            status=VacancyStatus.OPEN
        )
        return VacancyResponseDTO.from_orm(vacancy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/vacancies',
            response_model=List[VacancyResponseDTO],
            summary="Получение всех вакансий")
async def get_vacancies(
    open_only: bool = False,
    service: RecruitmentService = Depends(get_service)
):
    """
    Получение списка вакансий.
    
    open_only: если True, возвращает только открытые вакансии
    """
    if open_only:
        vacancies = service.get_open_vacancies()
    else:
        session = service.db.get_session()
        try:
            vacancies = session.query(Vacancy).all()
        finally:
            session.close()
    
    return [VacancyResponseDTO.from_orm(v) for v in vacancies]


@router.get('/vacancies/{vacancy_id}',
            response_model=VacancyResponseDTO,
            summary="Получение вакансии по ID")
async def get_vacancy(
    vacancy_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Получение информации о конкретной вакансии"""
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=404,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return VacancyResponseDTO.from_orm(vacancy)


@router.delete('/vacancies/{vacancy_id}',
               response_model=MessageDTO,
               summary="Удаление вакансии")
async def delete_vacancy(
    vacancy_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Удаление вакансии"""
    result = service.delete_vacancy(vacancy_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return MessageDTO(message="Вакансия успешно удалена")


# ========== RESUMES ==========

@router.post('/resumes',
             response_model=ResumeResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание резюме")
async def create_resume(
    resume_data: ResumeCreateDTO,
    user_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Создание резюме для кандидата"""
    session = service.db.get_session()
    try:
        resume = Resume(
            user_id=user_id,
            birth_date=resume_data.birth_date,
            contact_phone=resume_data.contact_phone,
            contact_email=resume_data.contact_email,
            education=resume_data.education,
            work_experience=resume_data.work_experience,
            skills=resume_data.skills
        )
        session.add(resume)
        session.commit()
        session.refresh(resume)
        return ResumeResponseDTO.from_orm(resume)
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@router.get('/resumes/user/{user_id}',
            response_model=ResumeResponseDTO,
            summary="Получение резюме пользователя")
async def get_user_resume(
    user_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Получение резюме конкретного пользователя"""
    session = service.db.get_session()
    try:
        resume = session.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise HTTPException(
                status_code=404,
                detail=f"Резюме для пользователя {user_id} не найдено"
            )
        return ResumeResponseDTO.from_orm(resume)
    finally:
        session.close()


# ========== INTERVIEWS ==========

@router.post('/interviews/stage1',
             response_model=InterviewStage1ResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание первого этапа собеседования")
async def create_interview_stage1(
    interview_data: InterviewStage1CreateDTO,
    hr_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Создание записи о первом этапе собеседования (soft skills)"""
    try:
        interview = service.create_interview_stage1(
            user_id=interview_data.user_id,
            hr_id=hr_id,
            vacancy_id=interview_data.vacancy_id,
            interview_date=interview_data.interview_date,
            questions=interview_data.questions,
            candidate_answers=interview_data.candidate_answers,
            soft_skills_score=interview_data.soft_skills_score,
            confidence_score=interview_data.confidence_score
        )
        return InterviewStage1ResponseDTO.from_orm(interview)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/interviews/stage1/candidate/{user_id}',
            response_model=List[InterviewStage1ResponseDTO],
            summary="Получение собеседований кандидата")
async def get_candidate_interviews(
    user_id: int,
    service: RecruitmentService = Depends(get_service)
):
    """Получение всех первых этапов собеседований кандидата"""
    interviews = service.get_interviews_stage1_by_candidate(user_id)
    return [InterviewStage1ResponseDTO.from_orm(i) for i in interviews]


# ========== STATISTICS ==========

@router.get('/statistics/overview',
            summary="Общая статистика системы")
async def get_statistics(service: RecruitmentService = Depends(get_service)):
    """Получение общей статистики по системе"""
    all_users = service.get_all_users()
    hr_users = service.get_all_users(role=UserRole.HR)
    candidates = service.get_all_users(role=UserRole.CANDIDATE)
    open_vacancies = service.get_open_vacancies()
    
    return {
        "total_users": len(all_users),
        "total_hr": len(hr_users),
        "total_candidates": len(candidates),
        "open_vacancies": len(open_vacancies),
        "timestamp": datetime.now()
    }

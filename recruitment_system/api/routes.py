#============================================================================
# Файл: api/routes.py
# Описание: Маршруты API (роутеры)
# ============================================================================

from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
import hashlib

# Импорты из вашего проекта
from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import UserRole, VacancyStatus
from api.dto import *
from api.auth import (
    LoginDTO, RegisterDTO, TokenDTO, CurrentUserDTO,  # ← Добавить!
    hash_password, verify_password, create_access_token,
    get_current_user, get_current_hr
)


# Инициализация
DATABASE_URL = 'sqlite:///recruitment.db'
db_repo = DatabaseRepository(DATABASE_URL)
db_repo.create_tables()  # Создаем таблицы если их нет

# Сервис для работы с БД
def get_service():
    """Dependency для получения сервиса"""
    return RecruitmentService(db_repo)


# Создаем роутер с префиксом /api
router = APIRouter(prefix='/api/v1', tags=['Simple HR Recruitment System'])


# ========== ENDPOINTS ДЛЯ USERS ==========

@router.post('/auth/register',
             response_model=TokenDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Регистрация нового пользователя",
             description="Регистрирует пользователя и возвращает JWT токен")
async def register(
    register_data: RegisterDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Регистрация нового пользователя"""
    
    # Проверяем что логин не занят
    existing_user = service.get_user_by_login(register_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Пользователь с логином '{register_data.login}' уже существует"
        )
    
    # Хешируем пароль
    password_hash = hash_password(register_data.password)
    
    # Конвертируем роль
    role = UserRole.HR if register_data.role == "HR" else UserRole.CANDIDATE
    
    # Создаем пользователя
    try:
        user = service.create_user(
            login=register_data.login,
            password_hash=password_hash,
            email=register_data.email,
            full_name=register_data.full_name,
            role=role
        )
        
        # Создаем JWT токен
        access_token = create_access_token(
            data={
                "sub": user.login,
                "user_id": user.user_id,
                "role": user.role.value
            }
        )
        
        return TokenDTO(
            access_token=access_token,
            user_id=user.user_id,
            role=user.role.value
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post('/auth/login',
             response_model=TokenDTO,
             summary="Вход в систему",
             description="Аутентификация пользователя и получение JWT токена")
async def login(
    login_data: LoginDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Вход в систему"""
    
    # Находим пользователя
    user = service.get_user_by_login(login_data.login)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Проверяем пароль
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем JWT токен
    access_token = create_access_token(
        data={
            "sub": user.login,
            "user_id": user.user_id,
            "role": user.role.value
        }
    )
    
    return TokenDTO(
        access_token=access_token,
        user_id=user.user_id,
        role=user.role.value
    )


@router.get('/auth/me',
            summary="Получение информации о текущем пользователе",
            description="Возвращает информацию из JWT токена")
async def get_me(current_user: CurrentUserDTO = Depends(get_current_user)):
    """Получение информации о текущем пользователе"""
    return {
        "user_id": current_user.user_id,
        "login": current_user.login,
        "role": current_user.role,
        "message": "Вы авторизованы"
    }



@router.get('/users', 
            response_model=List[UserResponseDTO],
            summary="Получение всех пользователей",
            description="Возвращает список всех пользователей с опциональной фильтрацией по роли")
async def get_all_users(
    role: Optional[UserRoleDTO] = None, 
    service: RecruitmentService = Depends(get_service)
):
    """Получение всех пользователей"""
    user_role = None
    if role:
        user_role = UserRole.HR if role == UserRoleDTO.HR else UserRole.CANDIDATE
    
    users = service.get_all_users(role=user_role)
    return [UserResponseDTO.from_orm(u) for u in users]


@router.get('/users/{user_id}', 
            response_model=UserResponseDTO,
            summary="Получение пользователя по ID",
            description="Возвращает информацию о конкретном пользователе")
async def get_user(user_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение пользователя по ID"""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return UserResponseDTO.from_orm(user)


@router.put('/users/{user_id}', 
            response_model=UserResponseDTO,
            summary="Обновление пользователя",
            description="Обновляет данные пользователя")
async def update_user(
    user_id: int, 
    user_data: UserUpdateDTO, 
    service: RecruitmentService = Depends(get_service)
):
    """Обновление пользователя"""
    update_dict = user_data.dict(exclude_unset=True)
    if not update_dict:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Не указаны поля для обновления"
        )
    
    user = service.update_user(user_id, **update_dict)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return UserResponseDTO.from_orm(user)


@router.delete('/users/{user_id}', 
            response_model=MessageResponseDTO,
            summary="Удаление пользователя",
            description="Удаляет пользователя из системы")
async def delete_user(user_id: int, service: RecruitmentService = Depends(get_service)):
    """Удаление пользователя"""
    result = service.delete_user(user_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return MessageResponseDTO(
        message="Пользователь успешно удален",
        detail=f"User ID: {user_id}"
    )


# ========== ENDPOINTS ДЛЯ VACANCIES ==========

@router.post('/vacancies', 
            response_model=VacancyResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание вакансии",
            description="Создает новую вакансию")
async def create_vacancy(vacancy_data: VacancyCreateDTO, service: RecruitmentService = Depends(get_service)):
    """Создание новой вакансии"""
    try:
        status_enum = VacancyStatus.OPEN if vacancy_data.status == VacancyStatusDTO.OPEN else \
                    VacancyStatus.CLOSED if vacancy_data.status == VacancyStatusDTO.CLOSED else \
                    VacancyStatus.ON_HOLD
        
        vacancy = service.create_vacancy(
            hr_id=vacancy_data.hr_id,
            position_title=vacancy_data.position_title,
            job_description=vacancy_data.job_description,
            requirements=vacancy_data.requirements,
            status=status_enum
        )
        return VacancyResponseDTO.from_orm(vacancy)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get('/vacancies', 
            response_model=List[VacancyResponseDTO],
            summary="Получение всех вакансий",
            description="Возвращает список всех вакансий или только открытых")
async def get_vacancies(
    open_only: bool = False,
    service: RecruitmentService = Depends(get_service)
):
    """Получение всех вакансий"""
    if open_only:
        vacancies = service.get_open_vacancies()
    else:
        # Получаем все вакансии через прямой запрос к БД
        session = service.db.get_session()
        try:
            from models.dao import Vacancy
            vacancies = session.query(Vacancy).all()
        finally:
            session.close()
    
    return [VacancyResponseDTO.from_orm(v) for v in vacancies]


@router.get('/vacancies/{vacancy_id}', 
            response_model=VacancyResponseDTO,
            summary="Получение вакансии по ID")
async def get_vacancy(vacancy_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение вакансии по ID"""
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return VacancyResponseDTO.from_orm(vacancy)


@router.put('/vacancies/{vacancy_id}', 
            response_model=VacancyResponseDTO,
            summary="Обновление вакансии")
async def update_vacancy(
    vacancy_id: int,
    vacancy_data: VacancyUpdateDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Обновление вакансии"""
    update_dict = vacancy_data.dict(exclude_unset=True)
    
    # Конвертируем status если он есть
    if 'status' in update_dict and update_dict['status']:
        status_dto = update_dict['status']
        update_dict['status'] = VacancyStatus.OPEN if status_dto == VacancyStatusDTO.OPEN else \
                                VacancyStatus.CLOSED if status_dto == VacancyStatusDTO.CLOSED else \
                                VacancyStatus.ON_HOLD
    
    vacancy = service.update_vacancy(vacancy_id, **update_dict)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return VacancyResponseDTO.from_orm(vacancy)


@router.patch('/vacancies/{vacancy_id}/close',
              response_model=VacancyResponseDTO,
              summary="Закрытие вакансии")
async def close_vacancy(vacancy_id: int, service: RecruitmentService = Depends(get_service)):
    """Закрытие вакансии"""
    vacancy = service.close_vacancy(vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return VacancyResponseDTO.from_orm(vacancy)


@router.delete('/vacancies/{vacancy_id}', 
               response_model=MessageResponseDTO,
               summary="Удаление вакансии")
async def delete_vacancy(vacancy_id: int, service: RecruitmentService = Depends(get_service)):
    """Удаление вакансии"""
    result = service.delete_vacancy(vacancy_id)
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return MessageResponseDTO(
        message="Вакансия успешно удалена",
        detail=f"Vacancy ID: {vacancy_id}"
    )


# ========== ENDPOINTS ДЛЯ INTERVIEWS STAGE 1 ==========

@router.post('/interviews/stage1',
             response_model=InterviewStage1ResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание первого этапа собеседования",
             description="Создает запись о первом этапе собеседования (soft skills)")
async def create_interview_stage1(
    interview_data: InterviewStage1CreateDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Создание первого этапа собеседования"""
    try:
        interview = service.create_interview_stage1(
            user_id=interview_data.user_id,
            hr_id=interview_data.hr_id,
            vacancy_id=interview_data.vacancy_id,
            interview_date=interview_data.interview_date,
            questions=interview_data.questions,
            candidate_answers=interview_data.candidate_answers,
            soft_skills_score=interview_data.soft_skills_score,
            confidence_score=interview_data.confidence_score
        )
        return InterviewStage1ResponseDTO.from_orm(interview)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get('/interviews/stage1/{interview_id}',
            response_model=InterviewStage1ResponseDTO,
            summary="Получение первого этапа по ID")
async def get_interview_stage1(interview_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение первого этапа по ID"""
    interview = service.get_interview_stage1_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Собеседование (этап 1) с ID {interview_id} не найдено"
        )
    return InterviewStage1ResponseDTO.from_orm(interview)


@router.get('/interviews/stage1/candidate/{user_id}',
            response_model=List[InterviewStage1ResponseDTO],
            summary="Получение всех первых этапов кандидата")
async def get_candidate_interviews_stage1(user_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение всех первых этапов собеседований кандидата"""
    interviews = service.get_interviews_stage1_by_candidate(user_id)
    return [InterviewStage1ResponseDTO.from_orm(i) for i in interviews]


# ========== ENDPOINTS ДЛЯ INTERVIEWS STAGE 2 ==========

@router.post('/interviews/stage2',
            response_model=InterviewStage2ResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание второго этапа собеседования",
            description="Создает запись о втором этапе собеседования (hard skills)")
async def create_interview_stage2(
    interview_data: InterviewStage2CreateDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Создание второго этапа собеседования"""
    try:
        interview = service.create_interview_stage2(
            user_id=interview_data.user_id,
            hr_id=interview_data.hr_id,
            interview1_id=interview_data.interview1_id,
            vacancy_id=interview_data.vacancy_id,
            interview_date=interview_data.interview_date,
            technical_tasks=interview_data.technical_tasks,
            candidate_solutions=interview_data.candidate_solutions,
            video_recording_path=interview_data.video_recording_path,
            hard_skills_score=interview_data.hard_skills_score,
            final_result=interview_data.final_result
        )
        return InterviewStage2ResponseDTO.from_orm(interview)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get('/interviews/stage2/{interview_id}',
            response_model=InterviewStage2ResponseDTO,
            summary="Получение второго этапа по ID")
async def get_interview_stage2(interview_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение второго этапа по ID"""
    interview = service.get_interview_stage2_by_id(interview_id)
    if not interview:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Собеседование (этап 2) с ID {interview_id} не найдено"
        )
    return InterviewStage2ResponseDTO.from_orm(interview)


# ========== ENDPOINTS ДЛЯ REPORTS ==========

@router.post('/reports',
            response_model=CandidateReportResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание отчета по кандидату",
            description="Генерирует итоговый отчет по кандидату после собеседований")
async def create_report(
    report_data: CandidateReportCreateDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Создание отчета по кандидату"""
    try:
        report = service.create_candidate_report(
            user_id=report_data.user_id,
            hr_id=report_data.hr_id,
            vacancy_id=report_data.vacancy_id,
            interview1_id=report_data.interview1_id,
            interview2_id=report_data.interview2_id,
            final_score=report_data.final_score,
            hr_recommendations=report_data.hr_recommendations
        )
        return CandidateReportResponseDTO.from_orm(report)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get('/reports/{report_id}',
            response_model=CandidateReportResponseDTO,
            summary="Получение отчета по ID")
async def get_report(report_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение отчета по ID"""
    report = service.get_report_by_id(report_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Отчет с ID {report_id} не найден"
        )
    return CandidateReportResponseDTO.from_orm(report)


@router.get('/reports/candidate/{user_id}',
            response_model=List[CandidateReportResponseDTO],
            summary="Получение всех отчетов кандидата")
async def get_candidate_reports(user_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение всех отчетов кандидата"""
    reports = service.get_reports_by_candidate(user_id)
    return [CandidateReportResponseDTO.from_orm(r) for r in reports]


@router.get('/reports/vacancy/{vacancy_id}',
            response_model=List[CandidateReportResponseDTO],
            summary="Получение всех отчетов по вакансии")
async def get_vacancy_reports(vacancy_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение всех отчетов по вакансии"""
    reports = service.get_reports_by_vacancy(vacancy_id)
    return [CandidateReportResponseDTO.from_orm(r) for r in reports]


# ========== ENDPOINTS ДЛЯ HR PROFILES ==========
@router.post('/hr/register',
             response_model=TokenDTO,
             status_code=status.HTTP_201_CREATED,
             summary="🎯 Регистрация HR-менеджера",
             description="Главный endpoint для регистрации HR. Создает пользователя и профиль за один запрос!")
async def register_hr(
    hr_data: HRRegisterDTO,
    service: RecruitmentService = Depends(get_service)
):
    """
    Регистрация HR-менеджера.
    
    Создает:
    1. Пользователя с ролью HR
    2. HR профиль с контактными данными
    
    Возвращает JWT токен для немедленного использования.
    """
    
    # 1. Проверяем что логин свободен
    existing_user = service.get_user_by_login(hr_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Логин '{hr_data.login}' уже занят"
        )
    
    # 2. Хешируем пароль
    password_hash = hash_password(hr_data.password)
    
    # 3. Создаем пользователя
    try:
        user = service.create_user(
            login=hr_data.login,
            password_hash=password_hash,
            email=hr_data.email,
            full_name=hr_data.full_name,
            role=UserRole.HR
        )
        
        # 4. Создаем HR профиль
        session = service.db.get_session()
        try:
            hr_profile = HRProfile(
                user_id=user.user_id,
                full_name=hr_data.full_name,
                position=hr_data.position,
                contact_phone=hr_data.contact_phone,
                company_name=hr_data.company_name
            )
            session.add(hr_profile)
            session.commit()
            session.refresh(hr_profile)
        finally:
            session.close()
        
        # 5. Генерируем JWT токен
        access_token = create_access_token(
            data={
                "sub": user.login,
                "user_id": user.user_id,
                "role": "HR",
                "hr_id": hr_profile.hr_id  # Добавляем hr_id в токен!
            }
        )
        
        return TokenDTO(
            access_token=access_token,
            user_id=user.user_id,
            role="HR"
        )
        
    except Exception as e:
        # Откатываем создание пользователя если профиль не создался
        if user:
            service.delete_user(user.user_id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ошибка при регистрации: {str(e)}"
        )


@router.post('/hr/login',
            response_model=TokenDTO,
            summary="🎯 Вход HR-менеджера",
            description="Аутентификация HR по логину и паролю")
async def login_hr(
    login_data: HRLoginDTO,
    service: RecruitmentService = Depends(get_service)
):
    """
    Вход HR-менеджера в систему.
    
    Проверяет:
    1. Существование пользователя
    2. Правильность пароля
    3. Наличие роли HR
    4. Наличие HR профиля
    """
    
    # 1. Ищем пользователя
    user = service.get_user_by_login(login_data.login)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # 2. Проверяем что это HR
    if user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Этот вход только для HR-менеджеров. Используйте вход для кандидатов."
        )
    
    # 3. Проверяем пароль
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # 4. Получаем HR профиль
    hr_profile = service.get_hr_profile_by_user_id(user.user_id)
    
    if not hr_profile:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="HR профиль не найден. Обратитесь в поддержку."
        )
    
    # 5. Создаем JWT токен
    access_token = create_access_token(
        data={
            "sub": user.login,
            "user_id": user.user_id,
            "role": "HR",
            "hr_id": hr_profile.hr_id  # hr_id в токене!
        }
    )
    
    return TokenDTO(
        access_token=access_token,
        user_id=user.user_id,
        role="HR"
    )


@router.get('/hr/profile',
            response_model=HRProfileFullDTO,
            summary="🎯 Профиль текущего HR",
            description="Получение полной информации о текущем HR-менеджере")
async def get_my_hr_profile_full(
    current_user: CurrentUserDTO = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение полного профиля текущего HR"""
    
    # Получаем пользователя и профиль
    user = service.get_user_by_id(current_user.user_id)
    hr_profile = service.get_hr_profile_by_user_id(current_user.user_id)
    
    if not hr_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HR профиль не найден"
        )
    
    # Считаем статистику
    all_vacancies = service.get_vacancies_by_hr(hr_profile.hr_id)
    active_vacancies = [v for v in all_vacancies if v.status == VacancyStatus.OPEN]
    
    return HRProfileFullDTO(
        # HR профиль
        hr_id=hr_profile.hr_id,
        full_name=hr_profile.full_name,
        position=hr_profile.position,
        contact_phone=hr_profile.contact_phone,
        company_name=hr_profile.company_name,
        created_at=hr_profile.created_at,
        # Пользователь
        user_id=user.user_id,
        login=user.login,
        email=user.email,
        registration_date=user.registration_date,
        # Статистика
        total_vacancies=len(all_vacancies),
        active_vacancies=len(active_vacancies)
    )


@router.get('/hr/dashboard',
            summary="🎯 Дашборд HR",
            description="Главная страница HR с полной статистикой")
async def get_hr_dashboard(
    current_user: CurrentUserDTO = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """
    Дашборд HR-менеджера с полной статистикой.
    
    Возвращает:
    - Профиль HR
    - Статистику по вакансиям
    - Статистику по собеседованиям
    - Последние активности
    """
    from models.dao import Vacancy, InterviewStage1, InterviewStage2, CandidateReport
    
    hr_profile = service.get_hr_profile_by_user_id(current_user.user_id)
    
    if not hr_profile:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="HR профиль не найден"
        )
    
    session = service.db.get_session()
    try:
        # Статистика по вакансиям
        all_vacancies = session.query(Vacancy).filter(
            Vacancy.hr_id == hr_profile.hr_id
        ).all()
        
        open_vacancies = [v for v in all_vacancies if v.status == VacancyStatus.OPEN]
        closed_vacancies = [v for v in all_vacancies if v.status == VacancyStatus.CLOSED]
        
        # Статистика по собеседованиям
        total_interviews_1 = session.query(InterviewStage1).filter(
            InterviewStage1.hr_id == hr_profile.hr_id
        ).count()
        
        total_interviews_2 = session.query(InterviewStage2).filter(
            InterviewStage2.hr_id == hr_profile.hr_id
        ).count()
        
        # Отчеты
        total_reports = session.query(CandidateReport).filter(
            CandidateReport.hr_id == hr_profile.hr_id
        ).count()
        
        # Последние вакансии
        recent_vacancies = session.query(Vacancy).filter(
            Vacancy.hr_id == hr_profile.hr_id
        ).order_by(Vacancy.created_at.desc()).limit(5).all()
        
        return {
            "hr_profile": {
                "hr_id": hr_profile.hr_id,
                "full_name": hr_profile.full_name,
                "position": hr_profile.position,
                "company_name": hr_profile.company_name
            },
            "statistics": {
                "vacancies": {
                    "total": len(all_vacancies),
                    "open": len(open_vacancies),
                    "closed": len(closed_vacancies)
                },
                "interviews": {
                    "stage1": total_interviews_1,
                    "stage2": total_interviews_2,
                    "conversion_rate": round(
                        (total_interviews_2 / total_interviews_1 * 100) if total_interviews_1 > 0 else 0,
                        2
                    )
                },
                "reports": total_reports
            },
            "recent_vacancies": [
                {
                    "vacancy_id": v.vacancy_id,
                    "position_title": v.position_title,
                    "status": v.status.value,
                    "created_at": v.created_at
                }
                for v in recent_vacancies
            ]
        }
        
    finally:
        session.close()

@router.post('/hr-profiles',
             response_model=HRProfileResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание профиля HR",
             description="⚠️ Требуется JWT токен. user_id берется из токена автоматически!")
async def create_hr_profile(
    profile_data: HRProfileCreateDTO,
    current_user: CurrentUserDTO = Depends(get_current_hr),  # 🔒 Только для HR
    service: RecruitmentService = Depends(get_service)
):
    """
    Создание профиля HR.
    
    user_id берется из JWT токена автоматически!
    Доступно только пользователям с ролью HR.
    """
    from models.dao import HRProfile
    
    # user_id берем из токена, а НЕ из запроса!
    user_id = current_user.user_id
    
    # Проверяем что профиль еще не создан
    session = service.db.get_session()
    try:
        existing_profile = session.query(HRProfile).filter(
            HRProfile.user_id == user_id
        ).first()
        
        if existing_profile:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У вас уже есть HR профиль"
            )
        
        profile = HRProfile(
            user_id=user_id,  # 🔑 Из токена!
            full_name=profile_data.full_name,
            position=profile_data.position,
            contact_phone=profile_data.contact_phone,
            company_name=profile_data.company_name
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)
        return HRProfileResponseDTO.from_orm(profile)
        
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        session.close()


@router.get('/hr-profiles/me',
            response_model=HRProfileResponseDTO,
            summary="Получение своего HR профиля",
            description="⚠️ Требуется JWT токен HR")
async def get_my_hr_profile(
    current_user: CurrentUserDTO = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение своего HR профиля"""
    from models.dao import HRProfile
    
    session = service.db.get_session()
    try:
        profile = session.query(HRProfile).filter(
            HRProfile.user_id == current_user.user_id
        ).first()
        
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="HR профиль не найден. Создайте профиль сначала."
            )
        
        return HRProfileResponseDTO.from_orm(profile)
    finally:
        session.close()


@router.get('/hr-profiles/{hr_id}',
            response_model=HRProfileResponseDTO,
            summary="Получение профиля HR")
async def get_hr_profile(hr_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение профиля HR"""
    from models.dao import HRProfile
    session = service.db.get_session()
    try:
        profile = session.query(HRProfile).filter(HRProfile.hr_id == hr_id).first()
        if not profile:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"HR профиль с ID {hr_id} не найден"
            )
        return HRProfileResponseDTO.from_orm(profile)
    finally:
        session.close()


# ========== ENDPOINTS ДЛЯ RESUMES ==========

@router.post('/resumes',
             response_model=ResumeResponseDTO,
             status_code=status.HTTP_201_CREATED,
             summary="Создание резюме",
             description="⚠️ Требуется токен кандидата. user_id берется из токена!")
async def create_resume(
    resume_data: ResumeCreateDTO,
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RecruitmentService = Depends(get_service)
):
    """Создание резюме (только кандидаты)"""
    
    # Проверяем роль
    if current_user.role != "Кандидат":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Только кандидаты могут создавать резюме"
        )
    
    from models.dao import Resume
    
    # user_id из токена!
    user_id = current_user.user_id
    
    session = service.db.get_session()
    try:
        # Проверяем что резюме еще нет
        existing = session.query(Resume).filter(Resume.user_id == user_id).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="У вас уже есть резюме"
            )
        
        resume = Resume(
            user_id=user_id,  # 🔑 Из токена!
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
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    finally:
        session.close()


@router.get('/resumes/me',
            response_model=ResumeResponseDTO,
            summary="Получение своего резюме")
async def get_my_resume(
    current_user: CurrentUserDTO = Depends(get_current_user),
    service: RecruitmentService = Depends(get_service)
):
    """Получение своего резюме"""
    from models.dao import Resume
    
    session = service.db.get_session()
    try:
        resume = session.query(Resume).filter(
            Resume.user_id == current_user.user_id
        ).first()
        
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Резюме не найдено. Создайте резюме сначала."
            )
        
        return ResumeResponseDTO.from_orm(resume)
    finally:
        session.close()


@router.get('/resumes/{resume_id}',
            response_model=ResumeResponseDTO,
            summary="Получение резюме")
async def get_resume(resume_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение резюме"""
    from models.dao import Resume
    session = service.db.get_session()
    try:
        resume = session.query(Resume).filter(Resume.resume_id == resume_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Резюме с ID {resume_id} не найдено"
            )
        return ResumeResponseDTO.from_orm(resume)
    finally:
        session.close()


@router.get('/resumes/user/{user_id}',
            response_model=ResumeResponseDTO,
            summary="Получение резюме пользователя")
async def get_user_resume(user_id: int, service: RecruitmentService = Depends(get_service)):
    """Получение резюме пользователя"""
    from models.dao import Resume
    session = service.db.get_session()
    try:
        resume = session.query(Resume).filter(Resume.user_id == user_id).first()
        if not resume:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Резюме для пользователя {user_id} не найдено"
            )
        return ResumeResponseDTO.from_orm(resume)
    finally:
        session.close()


# ========== СТАТИСТИКА И ДОПОЛНИТЕЛЬНЫЕ ENDPOINTS ==========

@router.get('/statistics/overview',
            summary="Общая статистика системы",
            description="Возвращает общую статистику по всей системе")
async def get_statistics(service: RecruitmentService = Depends(get_service)):
    """Общая статистика системы"""
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

@router.post('/candidates/register',
             response_model=TokenDTO,
             status_code=status.HTTP_201_CREATED,
             summary="👤 Регистрация кандидата",
             description="Регистрация кандидата (по приглашению от HR)")
async def register_candidate(
    candidate_data: RegisterDTO,
    service: RecruitmentService = Depends(get_service)
):
    """
    Регистрация кандидата.
    
    Обычно кандидаты регистрируются по приглашению от HR.
    """
    
    # Проверяем что это кандидат
    if candidate_data.role != "Кандидат":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Используйте /hr/register для регистрации HR"
        )
    
    # Проверяем логин
    existing_user = service.get_user_by_login(candidate_data.login)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Логин '{candidate_data.login}' уже занят"
        )
    
    # Создаем пользователя
    password_hash = hash_password(candidate_data.password)
    
    try:
        user = service.create_user(
            login=candidate_data.login,
            password_hash=password_hash,
            email=candidate_data.email,
            full_name=candidate_data.full_name,
            role=UserRole.CANDIDATE
        )
        
        # Токен
        access_token = create_access_token(
            data={
                "sub": user.login,
                "user_id": user.user_id,
                "role": "Кандидат"
            }
        )
        
        return TokenDTO(
            access_token=access_token,
            user_id=user.user_id,
            role="Кандидат"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post('/candidates/login',
             response_model=TokenDTO,
             summary="👤 Вход кандидата")
async def login_candidate(
    login_data: LoginDTO,
    service: RecruitmentService = Depends(get_service)
):
    """Вход кандидата в систему"""
    
    user = service.get_user_by_login(login_data.login)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # Проверяем что это кандидат
    if user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Этот вход только для кандидатов. Используйте /hr/login"
        )
    
    # Проверяем пароль
    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль"
        )
    
    # Токен
    access_token = create_access_token(
        data={
            "sub": user.login,
            "user_id": user.user_id,
            "role": "Кандидат"
        }
    )
    
    return TokenDTO(
        access_token=access_token,
        user_id=user.user_id,
        role="Кандидат"
    )


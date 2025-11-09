from fastapi import APIRouter, HTTPException, status, Depends
from typing import List, Optional
from datetime import datetime, timedelta

from config import settings
from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import User, UserRole, Vacancy, VacancyStatus, Resume, InterviewStage1, InterviewStage2, CandidateReport
from api.dto import *
from api.auth_utils import (
    get_password_hash, verify_password, create_access_token,
    get_current_user, get_current_hr, get_current_candidate
)

from fastapi import APIRouter, HTTPException, status, Depends, UploadFile, File, Form
from typing import List
import zipfile
import io
import secrets
import string
from datetime import datetime

from config import settings
from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from services.ai_utils import parse_resumes_with_deepseek, analyze_interview_answers
from services.media_utils import process_interview_video
from services.email_utils import send_bulk_invitations
from models.dao import User, UserRole, Vacancy, InterviewStage1
from api.auth_utils import get_current_hr, get_current_candidate, get_password_hash


from io import BytesIO
import zipfile
import pdfplumber
import secrets
import string
from datetime import datetime, date

# Инициализация
db_repo = DatabaseRepository(settings.DATABASE_URL)
db_repo.create_tables()

def get_service():
    return RecruitmentService(db_repo)

# Роутер
router = APIRouter(prefix='/api/v1', tags=['Simple HR API'])


# ========== AUTH & REGISTRATION ==========

@router.post('/register',
            response_model=TokenDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Регистрация нового пользователя",
            description="Регистрация HR или кандидата в системе")
async def register(
    user_data: UserRegisterDTO,
    service: RecruitmentService = Depends(get_service)
):
    """
    Регистрация нового пользователя (HR или кандидат).
    
    После успешной регистрации возвращается JWT токен для автоматического входа.
    """
    try:
        # Проверяем, существует ли пользователь
        existing_user = service.get_user_by_login(user_data.login)
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким логином уже существует"
            )
        
        existing_email = service.get_user_by_email(user_data.email)
        if existing_email:
            raise HTTPException(
                status_code=400,
                detail="Пользователь с таким email уже существует"
            )
        
        # Хешируем пароль
        password_hash = get_password_hash(user_data.password)
        
        # Конвертируем роль
        role = UserRole.HR if user_data.role == UserRoleDTO.HR else UserRole.CANDIDATE
        
        # Создаем пользователя
        user = service.create_user(
            login=user_data.login,
            password_hash=password_hash,
            email=user_data.email,
            full_name=user_data.full_name,
            role=role
        )
        
        # Создаем токен
        access_token = create_access_token(
            data={"sub": user.user_id, "role": user.role.value}
        )
        
        return TokenDTO(
            access_token=access_token,
            token_type="bearer",
            user_id=user.user_id,
            role=user.role.value,
            full_name=user.full_name
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post('/login',
            response_model=TokenDTO,
            summary="Вход в систему",
            description="Авторизация пользователя по логину и паролю")
async def login(
    credentials: UserLoginDTO,
    service: RecruitmentService = Depends(get_service)
):
    """
    Вход в систему.
    
    Возвращает JWT токен для дальнейшей аутентификации.
    """
    # Ищем пользователя
    user = service.get_user_by_login(credentials.login)
    
    if not user or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверный логин или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Создаем токен
    access_token = create_access_token(
        data={"sub": user.user_id, "role": user.role.value}
    )
    
    return TokenDTO(
        access_token=access_token,
        token_type="bearer",
        user_id=user.user_id,
        role=user.role.value,
        full_name=user.full_name
    )


@router.get('/me',
            response_model=UserProfileDTO,
            summary="Получение профиля текущего пользователя",
            description="Информация о текущем авторизованном пользователе")
async def get_my_profile(current_user: User = Depends(get_current_user)):
    """Получение профиля текущего пользователя из JWT токена"""
    return UserProfileDTO(
        user_id=current_user.user_id,
        login=current_user.login,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role.value,
        registration_date=current_user.registration_date
    )


# ========== USERS (только для HR) ==========

@router.get('/users',
            response_model=List[UserResponseDTO],
            summary="Получение всех пользователей",
            description="Доступно только для HR")
async def get_all_users(
    role: Optional[UserRoleDTO] = None,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение списка всех пользователей (только для HR)"""
    user_role = None
    if role:
        user_role = UserRole.HR if role == UserRoleDTO.HR else UserRole.CANDIDATE
    
    users = service.get_all_users(role=user_role)
    return [UserResponseDTO.from_orm(u) for u in users]


@router.get('/users/{user_id}',
            response_model=UserResponseDTO,
            summary="Получение пользователя по ID",
            description="Доступно только для HR")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение информации о пользователе (только для HR)"""
    user = service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(
            status_code=404,
            detail=f"Пользователь с ID {user_id} не найден"
        )
    return UserResponseDTO.from_orm(user)


# ========== VACANCIES ==========

@router.post('/vacancies',
            response_model=VacancyResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание вакансии",
            description="Создание новой вакансии (только для HR)")
async def create_vacancy(
    vacancy_data: VacancyWithQuestionsDTO,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Создание новой вакансии (только для HR)"""
    try:
        vacancy = service.create_vacancy(
            hr_id=current_user.user_id,
            position_title=vacancy_data.position_title,
            job_description=vacancy_data.job_description,
            requirements=vacancy_data.requirements,
            questions = vacancy_data.questions,
            status=VacancyStatus.OPEN
        )
        return VacancyResponseDTO.from_orm(vacancy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/vacancies',
            response_model=List[VacancyResponseDTO],
            summary="Получение всех вакансий",
            description="Доступно всем авторизованным пользователям")
async def get_vacancies(
    open_only: bool = False,
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_service)
):
    """Получение списка вакансий"""
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
    current_user: User = Depends(get_current_user),
    service: RecruitmentService = Depends(get_service)
):
    """Получение информации о вакансии"""
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(
            status_code=404,
            detail=f"Вакансия с ID {vacancy_id} не найдена"
        )
    return VacancyResponseDTO.from_orm(vacancy)


@router.put('/vacancies/{vacancy_id}',
            response_model=VacancyResponseDTO,
            summary="Обновление вакансии",
            description="Обновление вакансии (только для HR, который её создал)")
async def update_vacancy(
    vacancy_id: int,
    vacancy_data: VacancyUpdateDTO,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Обновление вакансии (только для HR, который её создал)"""
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    if vacancy.hr_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Вы можете редактировать только свои вакансии"
        )
    
    try:
        updated_vacancy = service.update_vacancy(vacancy_id, vacancy_data.dict(exclude_unset=True))
        return VacancyResponseDTO.from_orm(updated_vacancy)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete('/vacancies/{vacancy_id}',
            response_model=MessageDTO,
            summary="Удаление вакансии",
            description="Удаление вакансии (только для HR, который её создал)")
async def delete_vacancy(
    vacancy_id: int,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Удаление вакансии (только для HR, который её создал)"""
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    if vacancy.hr_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Вы можете удалять только свои вакансии"
        )
    
    result = service.delete_vacancy(vacancy_id)
    if not result:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    return MessageDTO(message="Вакансия успешно удалена")


# ========== RESUMES ==========

@router.post('/resumes',
            response_model=ResumeResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание резюме",
            description="Создание резюме (только для кандидатов)")
async def create_resume(
    resume_data: ResumeCreateDTO,
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """Создание резюме для текущего кандидата"""
    # Проверяем, есть ли уже резюме
    existing_resume = service.get_resume_by_user_id(current_user.user_id)
    if existing_resume:
        raise HTTPException(
            status_code=400,
            detail="У вас уже есть резюме. Используйте метод PUT для обновления"
        )
    
    session = service.db.get_session()
    try:
        resume = Resume(
            user_id=current_user.user_id,
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


@router.get('/resumes/my',
            response_model=ResumeResponseDTO,
            summary="Получение своего резюме",
            description="Получение резюме текущего кандидата")
async def get_my_resume(
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """Получение резюме текущего кандидата"""
    resume = service.get_resume_by_user_id(current_user.user_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail="Резюме не найдено. Создайте его сначала"
        )
    return ResumeResponseDTO.from_orm(resume)


@router.put('/resumes/my',
            response_model=ResumeResponseDTO,
            summary="Обновление своего резюме")
async def update_my_resume(
    resume_data: ResumeUpdateDTO,
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """Обновление резюме текущего кандидата"""
    session = service.db.get_session()
    try:
        resume = session.query(Resume).filter(Resume.user_id == current_user.user_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Резюме не найдено")
        
        update_data = resume_data.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(resume, key, value)
        
        session.commit()
        session.refresh(resume)
        return ResumeResponseDTO.from_orm(resume)
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        session.close()


@router.get('/resumes/user/{user_id}',
            response_model=ResumeResponseDTO,
            summary="Получение резюме кандидата",
            description="Получение резюме кандидата (только для HR)")
async def get_user_resume(
    user_id: int,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение резюме кандидата (только для HR)"""
    resume = service.get_resume_by_user_id(user_id)
    if not resume:
        raise HTTPException(
            status_code=404,
            detail=f"Резюме для пользователя {user_id} не найдено"
        )
    return ResumeResponseDTO.from_orm(resume)


# ========== INTERVIEWS ==========

@router.post('/interviews/stage1',
            response_model=InterviewStage1ResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание первого этапа собеседования",
            description="Только для HR")
async def create_interview_stage1(
    interview_data: InterviewStage1CreateDTO,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Создание записи о первом этапе собеседования (только для HR)"""
    try:
        interview = service.create_interview_stage1(
            candidate_id=interview_data.candidate_id,
            hr_id=current_user.user_id,
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


@router.post('/interviews/stage2',
            response_model=InterviewStage2ResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание второго этапа собеседования",
            description="Только для HR")
async def create_interview_stage2(
    interview_data: InterviewStage2CreateDTO,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Создание записи о втором этапе собеседования (только для HR)"""
    try:
        interview = service.create_interview_stage2(
            candidate_id=interview_data.candidate_id,
            hr_id=current_user.user_id,
            interview1_id=interview_data.interview1_id,
            vacancy_id=interview_data.vacancy_id,
            interview_date=interview_data.interview_date,
            technical_tasks=interview_data.technical_tasks,
            candidate_solutions=interview_data.candidate_solutions,
            hard_skills_score=interview_data.hard_skills_score
        )
        return InterviewStage2ResponseDTO.from_orm(interview)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/interviews/my',
            response_model=List[InterviewStage1ResponseDTO],
            summary="Получение моих собеседований",
            description="Кандидат видит свои собеседования")
async def get_my_interviews(
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """Получение собеседований текущего кандидата"""
    interviews = service.get_interviews_stage1_by_candidate(current_user.user_id)
    return [InterviewStage1ResponseDTO.from_orm(i) for i in interviews]


@router.get('/interviews/candidate/{candidate_id}',
            response_model=List[InterviewStage1ResponseDTO],
            summary="Получение собеседований кандидата",
            description="Только для HR")
async def get_candidate_interviews(
    candidate_id: int,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение всех собеседований кандидата (только для HR)"""
    interviews = service.get_interviews_stage1_by_candidate(candidate_id)
    return [InterviewStage1ResponseDTO.from_orm(i) for i in interviews]


# ========== REPORTS ==========

@router.post('/reports',
            response_model=ReportResponseDTO,
            status_code=status.HTTP_201_CREATED,
            summary="Создание отчета о кандидате",
            description="Только для HR")
async def create_report(
    report_data: ReportCreateDTO,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Создание отчета о кандидате (только для HR)"""
    try:
        report = service.create_candidate_report(
            candidate_id=report_data.candidate_id,
            hr_id=current_user.user_id,
            vacancy_id=report_data.vacancy_id,
            interview1_id=report_data.interview1_id,
            interview2_id=report_data.interview2_id,
            final_score=report_data.final_score,
            hr_recommendations=report_data.hr_recommendations
        )
        return ReportResponseDTO.from_orm(report)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get('/reports/my',
            response_model=List[ReportResponseDTO],
            summary="Получение моих отчетов",
            description="Кандидат видит отчеты о себе")
async def get_my_reports(
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """Получение отчетов о текущем кандидате"""
    reports = service.get_reports_by_candidate(current_user.user_id)
    return [ReportResponseDTO.from_orm(r) for r in reports]


@router.get('/reports/candidate/{candidate_id}',
            response_model=List[ReportResponseDTO],
            summary="Получение отчетов кандидата",
            description="Только для HR")
async def get_candidate_reports(
    candidate_id: int,
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение всех отчетов кандидата (только для HR)"""
    reports = service.get_reports_by_candidate(candidate_id)
    return [ReportResponseDTO.from_orm(r) for r in reports]


# ========== STATISTICS ==========

@router.get('/statistics/overview',
            summary="Общая статистика системы",
            description="Только для HR")
async def get_statistics(
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """Получение общей статистики по системе (только для HR)"""
    all_users = service.get_all_users()
    hr_users = service.get_all_users(role=UserRole.HR)
    candidates = service.get_all_users(role=UserRole.CANDIDATE)
    open_vacancies = service.get_open_vacancies()
    
    session = service.db.get_session()
    try:
        total_interviews = session.query(InterviewStage1).count()
        total_reports = session.query(CandidateReport).count()
    finally:
        session.close()
    
    return {
        "total_users": len(all_users),
        "total_hr": len(hr_users),
        "total_candidates": len(candidates),
        "open_vacancies": len(open_vacancies),
        "total_interviews": total_interviews,
        "total_reports": total_reports,
        "timestamp": datetime.now()
    }   


# ========== ЗАГРУЗКА РЕЗЮМЕ ==========

@router.post('/vacancies/{vacancy_id}/upload_resumes',
            summary="Загрузка резюме из ZIP архива",
            description="Загрузка ZIP с PDF резюме, парсинг через DeepSeek и создание кандидатов (только для HR)")
async def upload_resumes_zip(
    vacancy_id: int,
    zip_file: UploadFile = File(..., description="ZIP архив с PDF резюме"),
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """
    Загрузка и обработка резюме:
    1. Распаковка ZIP
    2. Извлечение PDF
    3. Парсинг через DeepSeek
    4. Создание пользователей-кандидатов
    """
    # Проверяем что вакансия существует и принадлежит текущему HR
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    if vacancy.hr_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Вы можете загружать резюме только для своих вакансий"
        )
    
    try:
        zip_bytes = await zip_file.read()
        pdf_texts = []

        with zipfile.ZipFile(BytesIO(zip_bytes)) as zip_ref:
            for file_info in zip_ref.filelist:
                if file_info.filename.lower().endswith('.pdf'):
                    pdf_data = zip_ref.read(file_info.filename)
                    try:
                        with pdfplumber.open(BytesIO(pdf_data)) as pdf:
                            text = ""
                            for page in pdf.pages:
                                text += page.extract_text() or ""
                            if text.strip():  # добавляем только если есть текст
                                pdf_texts.append(text)
                    except Exception as e:
                        print(f"Пропущен файл {file_info.filename}: {e}")

        if not pdf_texts:
            raise HTTPException(status_code=400, detail="В архиве нет корректных PDF с текстом")

        # Парсим резюме через DeepSeek
        parsed_resumes = await parse_resumes_with_deepseek(pdf_texts)
        
        # Создаем кандидатов
        created_candidates = []
        
        for resume_key, resume_data in parsed_resumes.items():
            try:
                # Генерируем логин и пароль
                candidate_number = len(created_candidates) + 1
                login = f"candidate_{datetime.now().timestamp()}_{candidate_number}"
                temp_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(12))
                password_hash = get_password_hash(temp_password)
                
                # Создаем пользователя
                user = service.create_user(
                    login=login,
                    password_hash=password_hash,
                    email=resume_data.get('contact_email', f"{login}@temp.com"),
                    full_name=resume_data.get('full_name', 'Неизвестно'),
                    role=UserRole.CANDIDATE
                )
                
                # Создаем резюме
                session = service.db.get_session()
                try:
                    from models.dao import Resume
                    from datetime import date
                    
                    birth_date = None
                    if resume_data.get('birth_date'):
                        try:
                            birth_date = date.fromisoformat(resume_data['birth_date'])
                        except:
                            pass
                    
                    resume = Resume(
                        user_id=user.user_id,
                        birth_date=birth_date,
                        contact_phone=resume_data.get('contact_phone'),
                        contact_email=resume_data.get('contact_email'),
                        education=resume_data.get('education'),
                        work_experience=resume_data.get('work_experience'),
                        skills=resume_data.get('skills')
                    )
                    session.add(resume)
                    session.commit()
                finally:
                    session.close()
                
                created_candidates.append({
                    "user_id": user.user_id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "login": login,
                    "password": temp_password
                })
            except:
                print('один из кандидатов не смог пройти проверку')
        
        return {
            "message": f"Успешно обработано {len(created_candidates)} резюме",
            "created_candidates": created_candidates,
            "total_processed": len(pdf_texts)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке резюме: {str(e)}"
        )


# ========== ПРИГЛАШЕНИЕ НА СОБЕСЕДОВАНИЕ ==========

@router.post('/interview/invite',
            summary="Приглашение кандидатов на собеседование",
            description="Отправка email приглашений выбранным кандидатам (только для HR)")
async def invite_candidates(
    candidate_ids: List[int] = Form(...),
    vacancy_id: int = Form(...),
    current_user: User = Depends(get_current_hr),
    service: RecruitmentService = Depends(get_service)
):
    """
    Отправка приглашений кандидатам:
    1. Проверка прав HR
    2. Получение данных кандидатов
    3. Отправка email с логином/паролем
    """
    # Проверяем вакансию
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    if vacancy.hr_id != current_user.user_id:
        raise HTTPException(
            status_code=403,
            detail="Вы можете приглашать кандидатов только на свои вакансии"
        )
    
    # Формируем приглашения
    invitations = []
    base_url = "http://localhost:8000"  # Загружать из настроек
    
    for candidate_id in candidate_ids:
        candidate = service.get_user_by_id(candidate_id)
        if not candidate or candidate.role != UserRole.CANDIDATE:
            continue
        
        resume = service.get_resume_by_user_id(candidate_id)
        if not resume:
            continue
        
        invitations.append({
            'email': candidate.email,
            'full_name': candidate.full_name,
            'position_title': vacancy.position_title,
            'vacancy_link': f"{base_url}/vacancies/{vacancy_id}/interview",
            'login': candidate.email,
            'password': "Пароль был отправлен при регистрации"
        })
    
    # Отправляем приглашения
    result = send_bulk_invitations(invitations)
    
    return {
        "message": "Приглашения отправлены",
        "total_invited": result['total'],
        "successful_invites": result['success'],
        "failed_invites": result['failed'],
        "failed_emails": result['failed_emails']
    }


# ========== ПРОХОЖДЕНИЕ ИНТЕРВЬЮ КАНДИДАТОМ ==========

@router.get('/vacancies/{vacancy_id}/interview',
            summary="Получение вопросов для интервью",
            description="Кандидат получает список вопросов для прохождения интервью")
async def get_interview_questions(
    vacancy_id: int,
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """
    Получение вопросов для интервью
    """
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    return {
        "vacancy_id": vacancy.vacancy_id,
        "position_title": vacancy.position_title,
        "job_description": vacancy.job_description,
        "requirements": vacancy.requirements,
        "questions": vacancy.questions or []
    }


@router.post('/vacancies/{vacancy_id}/submit_interview',
            summary="Отправка ответов на интервью",
            description="Кандидат отправляет видео и текстовые ответы на вопросы")
async def submit_interview_answers(
    vacancy_id: int,
    video_file: UploadFile = File(..., description="Видео файл с ответами (.mp4)"),
    text_answers: str = Form(..., description="Текстовые ответы на вопросы"),
    current_user: User = Depends(get_current_candidate),
    service: RecruitmentService = Depends(get_service)
):
    """
    Обработка интервью:
    1. Сохранение видео
    2. Конвертация MP4 → MP3
    3. Speech-to-Text
    4. Анализ через DeepSeek
    5. Сохранение оценок
    """
    vacancy = service.get_vacancy_by_id(vacancy_id)
    if not vacancy:
        raise HTTPException(status_code=404, detail="Вакансия не найдена")
    
    if not vacancy.questions:
        raise HTTPException(
            status_code=400,
            detail="Для этой вакансии не определены вопросы"
        )
    
    try:
        # Читаем видео
        video_bytes = await video_file.read()
        print(video_bytes,
            current_user.user_id,
            vacancy_id)
        
        # Обрабатываем видео (сохранение, конвертация, транскрибация)
        video_path, audio_path, transcribed_text = await process_interview_video(
            video_bytes,
            current_user.user_id,
            vacancy_id
        )
        
        # Объединяем текстовые и транскрибированные ответы
        combined_answers = f"{text_answers}\n\n[Из видео]:\n{transcribed_text}"
        
        # Анализируем ответы через DeepSeek
        soft_skills_score, confidence_score = await analyze_interview_answers(
            questions=vacancy.questions,
            answers=combined_answers,
            position_title=vacancy.position_title
        )
        
        # Создаем запись интервью
        interview = service.create_interview_stage1(
            candidate_id=current_user.user_id,
            hr_id=vacancy.hr_id,
            vacancy_id=vacancy_id,
            interview_date=datetime.now(),
            questions="\n".join([f"{i+1}. {q}" for i, q in enumerate(vacancy.questions)]),
            candidate_answers=combined_answers,
            soft_skills_score=soft_skills_score,
            confidence_score=confidence_score
        )
        
        # Обновляем пути к файлам
        session = service.db.get_session()
        try:
            db_interview = session.query(InterviewStage1).filter(
                InterviewStage1.interview1_id == interview.interview1_id
            ).first()
            db_interview.video_path = video_path
            db_interview.audio_path = audio_path
            session.commit()
        finally:
            session.close()
        
        return {
            "interview1_id": interview.interview1_id,
            "soft_skills_score": soft_skills_score,
            "confidence_score": confidence_score,
            "message": "Интервью успешно завершено и оценено"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при обработке интервью: {str(e)}"
        )
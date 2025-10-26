# Бизнес-логика для работы с БД (CRUD операции)


from typing import List, Optional, Dict, Any
from datetime import datetime

# Исправленные импорты
from models.dao import (
    User, UserRole, HRProfile, Resume, Vacancy, 
    VacancyStatus, InterviewStage1, InterviewStage2, 
    CandidateReport
)
from repository import DatabaseRepository


class RecruitmentService:
    """
    Сервис для работы с данными системы рекрутинга.
    Реализует все CRUD-операции.
    """
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db = db_repository
    
    # ========== CRUD для User ==========
    
    def create_user(
        self,
        login: str,
        password_hash: str,
        email: str,
        full_name: str,
        role: UserRole
    ) -> User:
        """Создание нового пользователя"""
        session = self.db.get_session()
        try:
            user = User(
                login=login,
                password_hash=password_hash,
                email=email,
                full_name=full_name,
                role=role
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        session = self.db.get_session()
        try:
            return session.query(User).filter(User.user_id == user_id).first()
        finally:
            session.close()
    
    def get_user_by_login(self, login: str) -> Optional[User]:
        """Получение пользователя по логину"""
        session = self.db.get_session()
        try:
            return session.query(User).filter(User.login == login).first()
        finally:
            session.close()
    
    def get_all_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Получение всех пользователей, опционально с фильтром по роли"""
        session = self.db.get_session()
        try:
            query = session.query(User)
            if role:
                query = query.filter(User.role == role)
            return query.all()
        finally:
            session.close()
    
    def update_user(self, user_id: int, **kwargs) -> Optional[User]:
        """Обновление данных пользователя"""
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                for key, value in kwargs.items():
                    if hasattr(user, key):
                        setattr(user, key, value)
                session.commit()
                session.refresh(user)
            return user
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        session = self.db.get_session()
        try:
            user = session.query(User).filter(User.user_id == user_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========== CRUD для Vacancy ==========
    
    def create_vacancy(
        self,
        hr_id: int,
        position_title: str,
        job_description: str,
        requirements: str,
        status: VacancyStatus = VacancyStatus.OPEN
    ) -> Vacancy:
        """Создание новой вакансии"""
        session = self.db.get_session()
        try:
            vacancy = Vacancy(
                hr_id=hr_id,
                position_title=position_title,
                job_description=job_description,
                requirements=requirements,
                status=status
            )
            session.add(vacancy)
            session.commit()
            session.refresh(vacancy)
            return vacancy
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_vacancy_by_id(self, vacancy_id: int) -> Optional[Vacancy]:
        """Получение вакансии по ID"""
        session = self.db.get_session()
        try:
            return session.query(Vacancy).filter(Vacancy.vacancy_id == vacancy_id).first()
        finally:
            session.close()
    
    def get_vacancies_by_hr(self, hr_id: int) -> List[Vacancy]:
        """Получение всех вакансий HR-менеджера"""
        session = self.db.get_session()
        try:
            return session.query(Vacancy).filter(Vacancy.hr_id == hr_id).all()
        finally:
            session.close()
    
    def get_open_vacancies(self) -> List[Vacancy]:
        """Получение всех открытых вакансий"""
        session = self.db.get_session()
        try:
            return session.query(Vacancy).filter(
                Vacancy.status == VacancyStatus.OPEN
            ).all()
        finally:
            session.close()
    
    def update_vacancy(self, vacancy_id: int, **kwargs) -> Optional[Vacancy]:
        """Обновление вакансии"""
        session = self.db.get_session()
        try:
            vacancy = session.query(Vacancy).filter(
                Vacancy.vacancy_id == vacancy_id
            ).first()
            if vacancy:
                for key, value in kwargs.items():
                    if hasattr(vacancy, key):
                        setattr(vacancy, key, value)
                session.commit()
                session.refresh(vacancy)
            return vacancy
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def close_vacancy(self, vacancy_id: int) -> Optional[Vacancy]:
        """Закрытие вакансии"""
        return self.update_vacancy(vacancy_id, status=VacancyStatus.CLOSED)
    
    def delete_vacancy(self, vacancy_id: int) -> bool:
        """Удаление вакансии"""
        session = self.db.get_session()
        try:
            vacancy = session.query(Vacancy).filter(
                Vacancy.vacancy_id == vacancy_id
            ).first()
            if vacancy:
                session.delete(vacancy)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========== CRUD для Interview Stage 1 ==========
    
    def create_interview_stage1(
        self,
        user_id: int,
        hr_id: int,
        vacancy_id: int,
        interview_date: datetime,
        questions: Optional[str] = None,
        candidate_answers: Optional[str] = None,
        soft_skills_score: Optional[int] = None,
        confidence_score: Optional[int] = None
    ) -> InterviewStage1:
        """Создание записи о первом этапе собеседования"""
        session = self.db.get_session()
        try:
            interview = InterviewStage1(
                user_id=user_id,
                hr_id=hr_id,
                vacancy_id=vacancy_id,
                interview_date=interview_date,
                questions=questions,
                candidate_answers=candidate_answers,
                soft_skills_score=soft_skills_score,
                confidence_score=confidence_score
            )
            session.add(interview)
            session.commit()
            session.refresh(interview)
            return interview
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_interview_stage1_by_id(self, interview1_id: int) -> Optional[InterviewStage1]:
        """Получение записи первого этапа по ID"""
        session = self.db.get_session()
        try:
            return session.query(InterviewStage1).filter(
                InterviewStage1.interview1_id == interview1_id
            ).first()
        finally:
            session.close()
    
    def get_interviews_stage1_by_candidate(self, user_id: int) -> List[InterviewStage1]:
        """Получение всех первых этапов собеседований кандидата"""
        session = self.db.get_session()
        try:
            return session.query(InterviewStage1).filter(
                InterviewStage1.user_id == user_id
            ).all()
        finally:
            session.close()
    
    def update_interview_stage1(
        self,
        interview1_id: int,
        **kwargs
    ) -> Optional[InterviewStage1]:
        """Обновление записи первого этапа"""
        session = self.db.get_session()
        try:
            interview = session.query(InterviewStage1).filter(
                InterviewStage1.interview1_id == interview1_id
            ).first()
            if interview:
                for key, value in kwargs.items():
                    if hasattr(interview, key):
                        setattr(interview, key, value)
                session.commit()
                session.refresh(interview)
            return interview
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    # ========== CRUD для Interview Stage 2 ==========
    
    def create_interview_stage2(
        self,
        user_id: int,
        hr_id: int,
        interview1_id: int,
        vacancy_id: int,
        interview_date: datetime,
        technical_tasks: Optional[str] = None,
        candidate_solutions: Optional[str] = None,
        video_recording_path: Optional[str] = None,
        hard_skills_score: Optional[int] = None,
        final_result: Optional[str] = None
    ) -> InterviewStage2:
        """Создание записи о втором этапе собеседования"""
        session = self.db.get_session()
        try:
            interview = InterviewStage2(
                user_id=user_id,
                hr_id=hr_id,
                interview1_id=interview1_id,
                vacancy_id=vacancy_id,
                interview_date=interview_date,
                technical_tasks=technical_tasks,
                candidate_solutions=candidate_solutions,
                video_recording_path=video_recording_path,
                hard_skills_score=hard_skills_score,
                final_result=final_result
            )
            session.add(interview)
            session.commit()
            session.refresh(interview)
            return interview
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_interview_stage2_by_id(self, interview2_id: int) -> Optional[InterviewStage2]:
        """Получение записи второго этапа по ID"""
        session = self.db.get_session()
        try:
            return session.query(InterviewStage2).filter(
                InterviewStage2.interview2_id == interview2_id
            ).first()
        finally:
            session.close()
    
    # ========== CRUD для Candidate Report ==========
    
    def create_candidate_report(
        self,
        user_id: int,
        hr_id: int,
        vacancy_id: int,
        interview1_id: Optional[int] = None,
        interview2_id: Optional[int] = None,
        final_score: Optional[float] = None,
        hr_recommendations: Optional[str] = None
    ) -> CandidateReport:
        """Создание отчета по кандидату"""
        session = self.db.get_session()
        try:
            report = CandidateReport(
                user_id=user_id,
                hr_id=hr_id,
                vacancy_id=vacancy_id,
                interview1_id=interview1_id,
                interview2_id=interview2_id,
                final_score=final_score,
                hr_recommendations=hr_recommendations
            )
            session.add(report)
            session.commit()
            session.refresh(report)
            return report
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_report_by_id(self, report_id: int) -> Optional[CandidateReport]:
        """Получение отчета по ID"""
        session = self.db.get_session()
        try:
            return session.query(CandidateReport).filter(
                CandidateReport.report_id == report_id
            ).first()
        finally:
            session.close()
    
    def get_reports_by_candidate(self, user_id: int) -> List[CandidateReport]:
        """Получение всех отчетов кандидата"""
        session = self.db.get_session()
        try:
            return session.query(CandidateReport).filter(
                CandidateReport.user_id == user_id
            ).all()
        finally:
            session.close()
    
    def get_reports_by_vacancy(self, vacancy_id: int) -> List[CandidateReport]:
        """Получение всех отчетов по вакансии"""
        session = self.db.get_session()
        try:
            return session.query(CandidateReport).filter(
                CandidateReport.vacancy_id == vacancy_id
            ).all()
        finally:
            session.close()
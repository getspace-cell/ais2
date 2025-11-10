from typing import List, Optional
from datetime import datetime, date
from models.dao import (
    User, UserRole, Resume, Vacancy, VacancyStatus,
    InterviewStage1, InterviewStage2, CandidateReport
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
        """Создание пользователя"""
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
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Получение пользователя по email"""
        session = self.db.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        finally:
            session.close()
    
    def get_all_users(self, role: Optional[UserRole] = None) -> List[User]:
        """Получение всех пользователей с фильтрацией по роли"""
        session = self.db.get_session()
        try:
            query = session.query(User)
            if role:
                query = query.filter(User.role == role)
            return query.all()
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
    
    # ========== CRUD для Resume ==========
    
    def create_resume(
        self,
        user_id: int,
        birth_date: Optional[date] = None,
        contact_phone: Optional[str] = None,
        contact_email: Optional[str] = None,
        education: Optional[str] = None,
        work_experience: Optional[str] = None,
        skills: Optional[str] = None
    ) -> Resume:
        """Создание резюме для кандидата"""
        session = self.db.get_session()
        try:
            resume = Resume(
                user_id=user_id,
                birth_date=birth_date,
                contact_phone=contact_phone,
                contact_email=contact_email,
                education=education,
                work_experience=work_experience,
                skills=skills
            )
            session.add(resume)
            session.commit()
            session.refresh(resume)
            return resume
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_resume_by_user_id(self, user_id: int) -> Optional[Resume]:
        """Получение резюме кандидата"""
        session = self.db.get_session()
        try:
            return session.query(Resume).filter(Resume.user_id == user_id).first()
        finally:
            session.close()
    
    # ========== CRUD для Vacancy ==========
    
    def create_vacancy(
        self,
        hr_id: int,
        position_title: str,
        job_description: Optional[str] = None,
        requirements: Optional[str] = None,
        questions: Optional[str] = None,
        status: VacancyStatus = VacancyStatus.OPEN
    ) -> Vacancy:
        """Создание вакансии"""
        session = self.db.get_session()
        try:
            vacancy = Vacancy(
                hr_id=hr_id,
                position_title=position_title,
                job_description=job_description,
                requirements=requirements,
                questions = questions,
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
    
    def get_all_vacancies(self) -> List[Vacancy]:
        """Получение всех вакансий"""
        session = self.db.get_session()
        try:
            return session.query(Vacancy).all()
        finally:
            session.close()
    
    def get_open_vacancies(self) -> List[Vacancy]:
        """Получение открытых вакансий"""
        session = self.db.get_session()
        try:
            return session.query(Vacancy).filter(
                Vacancy.status == VacancyStatus.OPEN
            ).all()
        finally:
            session.close()
    
    def update_vacancy(self, vacancy_id: int, update_data: dict) -> Optional[Vacancy]:
        """Обновление вакансии"""
        session = self.db.get_session()
        try:
            vacancy = session.query(Vacancy).filter(Vacancy.vacancy_id == vacancy_id).first()
            if not vacancy:
                return None
            
            for key, value in update_data.items():
                if value is not None:
                    setattr(vacancy, key, value)
            
            session.commit()
            session.refresh(vacancy)
            return vacancy
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def delete_vacancy(self, vacancy_id: int) -> bool:
        """Удаление вакансии"""
        session = self.db.get_session()
        try:
            vacancy = session.query(Vacancy).filter(Vacancy.vacancy_id == vacancy_id).first()
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
    
    # ========== CRUD для InterviewStage1 ==========
    
    def create_interview_stage1(
        self,
        candidate_id: int,
        hr_id: int,
        vacancy_id: int,
        interview_date: datetime,
        questions: Optional[str] = None,
        candidate_answers: Optional[str] = None,
        soft_skills_score: Optional[int] = None,
        confidence_score: Optional[int] = None
    ) -> InterviewStage1:
        """Создание первого этапа собеседования"""
        session = self.db.get_session()
        try:
            interview = InterviewStage1(
                candidate_id=candidate_id,
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
        """Получение первого этапа по ID"""
        session = self.db.get_session()
        try:
            return session.query(InterviewStage1).filter(
                InterviewStage1.interview1_id == interview1_id
            ).first()
        finally:
            session.close()
    
    def get_interviews_stage1_by_candidate(self, candidate_id: int) -> List[InterviewStage1]:
        """Получение всех первых этапов кандидата"""
        session = self.db.get_session()
        try:
            return session.query(InterviewStage1).filter(
                InterviewStage1.candidate_id == candidate_id
            ).all()
        finally:
            session.close()
    
    # ========== CRUD для InterviewStage2 ==========
    
    def create_interview_stage2(
        self,
        candidate_id: int,
        hr_id: int,
        interview1_id: int,
        vacancy_id: int,
        interview_date: datetime,
        technical_tasks: Optional[str] = None,
        candidate_solutions: Optional[str] = None,
        hard_skills_score: Optional[int] = None
    ) -> InterviewStage2:
        """Создание второго этапа собеседования"""
        session = self.db.get_session()
        try:
            interview = InterviewStage2(
                candidate_id=candidate_id,
                hr_id=hr_id,
                interview1_id=interview1_id,
                vacancy_id=vacancy_id,
                interview_date=interview_date,
                technical_tasks=technical_tasks,
                candidate_solutions=candidate_solutions,
                hard_skills_score=hard_skills_score
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
    
    # ========== CRUD для CandidateReport ==========
    
    def create_candidate_report(
        self,
        candidate_id: int,
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
                candidate_id=candidate_id,
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
    
    def get_reports_by_candidate(self, candidate_id: int) -> List[CandidateReport]:
        """Получение всех отчетов кандидата"""
        session = self.db.get_session()
        try:
            return session.query(CandidateReport).filter(
                CandidateReport.candidate_id == candidate_id
            ).all()
        finally:
            session.close()
    
    def create_interview_stage1_invitation(
        self,
        candidate_id: int,
        hr_id: int,
        vacancy_id: int
    ) -> InterviewStage1:
        """
        Создание записи интервью при приглашении кандидата.
        Заполняются только обязательные поля (candidate_id, hr_id, vacancy_id).
        Остальные поля заполнятся при прохождении интервью.
        """
        session = self.db.get_session()
        try:
            interview = InterviewStage1(
                candidate_id=candidate_id,
                hr_id=hr_id,
                vacancy_id=vacancy_id,
                # Остальные поля остаются NULL до прохождения интервью
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


    def get_pending_interview(
        self,
        candidate_id: int,
        vacancy_id: int
    ) -> Optional[InterviewStage1]:
        """
        Получение незавершенного интервью кандидата.
        Незавершенное = когда interview_date = NULL (еще не прошел интервью).
        """
        session = self.db.get_session()
        try:
            return session.query(InterviewStage1).filter(
                InterviewStage1.candidate_id == candidate_id,
                InterviewStage1.vacancy_id == vacancy_id,
                InterviewStage1.interview_date == None  # Незавершенное интервью
            ).first()
        finally:
            session.close()


    def update_interview_stage1_completion(
        self,
        interview1_id: int,
        interview_date: datetime,
        questions: str,
        candidate_answers: str,
        video_path: str,
        audio_path: str,
        soft_skills_score: int,
        confidence_score: int
    ) -> InterviewStage1:
        """
        Обновление записи интервью после прохождения кандидатом.
        Заполняются все оставшиеся поля.
        """
        session = self.db.get_session()
        try:
            interview = session.query(InterviewStage1).filter(
                InterviewStage1.interview1_id == interview1_id
            ).first()
            
            if not interview:
                raise ValueError(f"Интервью с ID {interview1_id} не найдено")
            
            # Обновляем поля
            interview.interview_date = interview_date
            interview.questions = questions
            interview.candidate_answers = candidate_answers
            interview.video_path = video_path
            interview.audio_path = audio_path
            interview.soft_skills_score = soft_skills_score
            interview.confidence_score = confidence_score
            
            session.commit()
            session.refresh(interview)
            return interview
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
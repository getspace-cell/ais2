from typing import List, Optional
from datetime import datetime
from datetime import date
from models.dao import (
    UserProfile, Resume, HRProfile, HRAdditionalInfo,
    Vacancy, VacancyStatus, InterviewStage1, InterviewStage2,
    CandidateReport
)
from repository import DatabaseRepository


class RecruitmentService:
    """
    Сервис для работы с данными системы рекрутинга.
    Реализует все CRUD-операции для новой архитектуры.
    """
    
    def __init__(self, db_repository: DatabaseRepository):
        self.db = db_repository
    
    # ========== CRUD для UserProfile (Кандидаты) ==========
    
    def create_user_profile(
        self,
        login: str,
        password_hash: str,
        email: str
    ) -> UserProfile:
        """Создание профиля кандидата"""
        session = self.db.get_session()
        try:
            user = UserProfile(
                login=login,
                password_hash=password_hash,
                email=email
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
    
    def get_user_profile_by_id(self, user_id: int) -> Optional[UserProfile]:
        """Получение профиля кандидата по ID"""
        session = self.db.get_session()
        try:
            return session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        finally:
            session.close()
    
    def get_user_profile_by_login(self, login: str) -> Optional[UserProfile]:
        """Получение профиля кандидата по логину"""
        session = self.db.get_session()
        try:
            return session.query(UserProfile).filter(UserProfile.login == login).first()
        finally:
            session.close()
    
    def get_all_user_profiles(self) -> List[UserProfile]:
        """Получение всех профилей кандидатов"""
        session = self.db.get_session()
        try:
            return session.query(UserProfile).all()
        finally:
            session.close()
    
    def delete_user_profile(self, user_id: int) -> bool:
        """Удаление профиля кандидата"""
        session = self.db.get_session()
        try:
            user = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
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
        full_name: str,
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
                full_name=full_name,
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
    
    # ========== CRUD для HRProfile ==========
    
    def create_hr_profile(
        self,
        login: str,
        password_hash: str,
        email: str
    ) -> HRProfile:
        """Создание профиля HR"""
        session = self.db.get_session()
        try:
            hr = HRProfile(
                login=login,
                password_hash=password_hash,
                email=email
            )
            session.add(hr)
            session.commit()
            session.refresh(hr)
            return hr
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_hr_profile_by_id(self, hr_id: int) -> Optional[HRProfile]:
        """Получение профиля HR по ID"""
        session = self.db.get_session()
        try:
            return session.query(HRProfile).filter(HRProfile.hr_id == hr_id).first()
        finally:
            session.close()
    
    def get_hr_profile_by_login(self, login: str) -> Optional[HRProfile]:
        """Получение профиля HR по логину"""
        session = self.db.get_session()
        try:
            return session.query(HRProfile).filter(HRProfile.login == login).first()
        finally:
            session.close()
    
    # ========== CRUD для HRAdditionalInfo ==========
    
    def create_hr_additional_info(
        self,
        hr_id: int,
        full_name: str,
        position: Optional[str] = None,
        contact_phone: Optional[str] = None,
        company_name: Optional[str] = None
    ) -> HRAdditionalInfo:
        """Создание дополнительной информации HR"""
        session = self.db.get_session()
        try:
            info = HRAdditionalInfo(
                hr_id=hr_id,
                full_name=full_name,
                position=position,
                contact_phone=contact_phone,
                company_name=company_name
            )
            session.add(info)
            session.commit()
            session.refresh(info)
            return info
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_hr_additional_info(self, hr_id: int) -> Optional[HRAdditionalInfo]:
        """Получение дополнительной информации HR"""
        session = self.db.get_session()
        try:
            return session.query(HRAdditionalInfo).filter(
                HRAdditionalInfo.hr_id == hr_id
            ).first()
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
                questions=questions,
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
        user_id: int,
        hr_id: int,
        vacancy_id: int,
        interview_date: datetime,
        questions: Optional[str] = None,
        candidate_answers: Optional[str] = None,
        video_recording_path: Optional[str] = None,
        soft_skills_score: Optional[int] = None
    ) -> InterviewStage1:
        """Создание первого этапа собеседования"""
        session = self.db.get_session()
        try:
            interview = InterviewStage1(
                user_id=user_id,
                hr_id=hr_id,
                vacancy_id=vacancy_id,
                interview_date=interview_date,
                questions=questions,
                candidate_answers=candidate_answers,
                video_recording_path=video_recording_path,
                soft_skills_score=soft_skills_score
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
    
    # ========== CRUD для InterviewStage2 ==========
    
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
        hard_skills_score: Optional[int] = None
    ) -> InterviewStage2:
        """Создание второго этапа собеседования"""
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
    
    def get_reports_by_candidate(self, user_id: int) -> List[CandidateReport]:
        """Получение всех отчетов кандидата"""
        session = self.db.get_session()
        try:
            return session.query(CandidateReport).filter(
                CandidateReport.user_id == user_id
            ).all()
        finally:
            session.close()
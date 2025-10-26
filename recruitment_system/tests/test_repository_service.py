#Тесты для проверки CRUD-операций

import unittest
import sys
from pathlib import Path
from datetime import datetime

# Добавляем родительскую директорию в путь для импортов
sys.path.insert(0, str(Path(__file__).parent.parent))

from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import (
    User, UserRole, HRProfile, Resume, Vacancy, 
    VacancyStatus, InterviewStage1, InterviewStage2, 
    CandidateReport
)

class TestRecruitmentService(unittest.TestCase):
    """Тесты для сервиса рекрутинга"""
    
    @classmethod
    def setUpClass(cls):
        """Инициализация перед всеми тестами"""
        # SQLite для тестирования
        cls.db_repo = DatabaseRepository('sqlite:///test_recruitment.db')
        cls.db_repo.create_tables()
        cls.service = RecruitmentService(cls.db_repo)
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после всех тестов"""
        cls.db_repo.drop_tables()
    
    def test_01_create_user(self):
        """Тест создания пользователя"""
        user = self.service.create_user(
            login="hr_ivan",
            password_hash="hashed_password",
            email="ivan@company.com",
            full_name="Иванов Иван",
            role=UserRole.HR
        )
        self.assertIsNotNone(user.user_id)
        self.assertEqual(user.login, "hr_ivan")
        self.assertEqual(user.role, UserRole.HR)
    
    def test_02_get_user_by_id(self):
        """Тест получения пользователя по ID"""
        user = self.service.get_user_by_login("hr_ivan")
        self.assertIsNotNone(user)
        
        fetched_user = self.service.get_user_by_id(user.user_id)
        self.assertEqual(fetched_user.login, "hr_ivan")
    
    def test_03_update_user(self):
        """Тест обновления пользователя"""
        user = self.service.get_user_by_login("hr_ivan")
        updated = self.service.update_user(
            user.user_id,
            email="new_email@company.com"
        )
        self.assertEqual(updated.email, "new_email@company.com")
    
    def test_04_create_candidate(self):
        """Тест создания кандидата"""
        candidate = self.service.create_user(
            login="candidate_anna",
            password_hash="hashed_pass",
            email="anna@mail.com",
            full_name="Петрова Анна",
            role=UserRole.CANDIDATE
        )
        self.assertEqual(candidate.role, UserRole.CANDIDATE)
    
    def test_05_create_vacancy(self):
        """Тест создания вакансии"""
        hr = self.service.get_user_by_login("hr_ivan")
        
        # Создаем HR профиль
        session = self.service.db.get_session()
        try:
            hr_profile = HRProfile(
                user_id=hr.user_id,
                full_name="Иванов Иван",
                position="HR Manager",
                contact_phone="+7-900-123-45-67",
                company_name="Tech Corp"
            )
            session.add(hr_profile)
            session.commit()
            session.refresh(hr_profile)
            hr_id = hr_profile.hr_id
        finally:
            session.close()
        
        vacancy = self.service.create_vacancy(
            hr_id=hr_id,
            position_title="Python Developer",
            job_description="Разработка backend на Python",
            requirements="Python 3.9+, SQLAlchemy, FastAPI"
        )
        self.assertIsNotNone(vacancy.vacancy_id)
        self.assertEqual(vacancy.position_title, "Python Developer")
    
    def test_06_get_open_vacancies(self):
        """Тест получения открытых вакансий"""
        vacancies = self.service.get_open_vacancies()
        self.assertGreater(len(vacancies), 0)
    
    def test_07_create_interview_stage1(self):
        """Тест создания первого этапа собеседования"""
        candidate = self.service.get_user_by_login("candidate_anna")
        hr = self.service.get_user_by_login("hr_ivan")
        
        # Получаем HR профиль
        session = self.service.db.get_session()
        try:
            hr_profile = session.query(HRProfile).filter(
                HRProfile.user_id == hr.user_id
            ).first()
            hr_id = hr_profile.hr_id
        finally:
            session.close()
        
        vacancies = self.service.get_open_vacancies()
        
        interview = self.service.create_interview_stage1(
            user_id=candidate.user_id,
            hr_id=hr_id,
            vacancy_id=vacancies[0].vacancy_id,
            interview_date=datetime.now(),
            questions="Расскажите о себе. Почему хотите работать у нас?",
            candidate_answers="Я опытный разработчик...",
            soft_skills_score=85,
            confidence_score=90
        )
        self.assertIsNotNone(interview.interview1_id)
        self.assertEqual(interview.soft_skills_score, 85)
    
    def test_08_create_interview_stage2(self):
        """Тест создания второго этапа собеседования"""
        candidate = self.service.get_user_by_login("candidate_anna")
        interviews = self.service.get_interviews_stage1_by_candidate(candidate.user_id)
        interview1 = interviews[0]
        
        interview2 = self.service.create_interview_stage2(
            user_id=candidate.user_id,
            hr_id=interview1.hr_id,
            interview1_id=interview1.interview1_id,
            vacancy_id=interview1.vacancy_id,
            interview_date=datetime.now(),
            technical_tasks="Реализовать REST API",
            candidate_solutions="Код решения...",
            hard_skills_score=88,
            final_result="Принят"
        )
        self.assertIsNotNone(interview2.interview2_id)
        self.assertEqual(interview2.final_result, "Принят")
    
    def test_09_create_candidate_report(self):
        """Тест создания отчета по кандидату"""
        candidate = self.service.get_user_by_login("candidate_anna")
        interviews1 = self.service.get_interviews_stage1_by_candidate(candidate.user_id)
        interview1 = interviews1[0]
        
        session = self.service.db.get_session()
        try:
            interview2 = session.query(InterviewStage2).filter(
                InterviewStage2.interview1_id == interview1.interview1_id
            ).first()
            interview2_id = interview2.interview2_id
        finally:
            session.close()
        
        # Рассчитываем итоговый балл
        final_score = (interview1.soft_skills_score + interview2.hard_skills_score) / 2
        
        report = self.service.create_candidate_report(
            user_id=candidate.user_id,
            hr_id=interview1.hr_id,
            vacancy_id=interview1.vacancy_id,
            interview1_id=interview1.interview1_id,
            interview2_id=interview2_id,
            final_score=final_score,
            hr_recommendations="Рекомендуется к найму. Сильные технические навыки."
        )
        self.assertIsNotNone(report.report_id)
        self.assertAlmostEqual(report.final_score, 86.5, places=1)
    
    def test_10_get_reports_by_vacancy(self):
        """Тест получения отчетов по вакансии"""
        vacancies = self.service.get_open_vacancies()
        reports = self.service.get_reports_by_vacancy(vacancies[0].vacancy_id)
        self.assertGreater(len(reports), 0)
    
    def test_11_close_vacancy(self):
        """Тест закрытия вакансии"""
        vacancies = self.service.get_open_vacancies()
        vacancy = self.service.close_vacancy(vacancies[0].vacancy_id)
        self.assertEqual(vacancy.status, VacancyStatus.CLOSED)
    
    def test_12_delete_user(self):
        """Тест удаления пользователя (должен быть последним)"""
        # Создаем временного пользователя для удаления
        temp_user = self.service.create_user(
            login="temp_user",
            password_hash="temp_pass",
            email="temp@test.com",
            full_name="Временный Пользователь",
            role=UserRole.CANDIDATE
        )
        user_id = temp_user.user_id
        
        result = self.service.delete_user(user_id)
        self.assertTrue(result)
        
        deleted_user = self.service.get_user_by_id(user_id)
        self.assertIsNone(deleted_user)


if __name__ == '__main__':
    unittest.main()

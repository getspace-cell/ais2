import unittest
import sys
from pathlib import Path
from datetime import datetime, date

sys.path.insert(0, str(Path(__file__).parent.parent))

from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import (
    UserProfile, Resume, HRProfile, HRAdditionalInfo,
    Vacancy, VacancyStatus, InterviewStage1, InterviewStage2,
    CandidateReport
)


class TestRecruitmentService(unittest.TestCase):
    """Тесты для сервиса рекрутинга"""
    
    @classmethod
    def setUpClass(cls):
        """Инициализация перед всеми тестами"""
        cls.db_repo = DatabaseRepository('sqlite:///test_simple_hr.db')
        cls.db_repo.create_tables()
        cls.service = RecruitmentService(cls.db_repo)
    
    @classmethod
    def tearDownClass(cls):
        """Очистка после всех тестов"""
        cls.db_repo.drop_tables()
    
    def test_01_create_user_profile(self):
        """Тест создания профиля кандидата"""
        user = self.service.create_user_profile(
            login="test_candidate",
            password_hash="hash123",
            email="candidate@test.com"
        )
        self.assertIsNotNone(user.user_id)
        self.assertEqual(user.login, "test_candidate")
    
    def test_02_create_resume(self):
        """Тест создания резюме"""
        user = self.service.get_user_profile_by_login("test_candidate")
        
        resume = self.service.create_resume(
            user_id=user.user_id,
            full_name="Тестовый Кандидат",
            birth_date=date(1990, 1, 1),
            contact_phone="+7-900-000-00-00",
            contact_email="candidate@test.com",
            education="Тестовый Университет",
            work_experience="5 лет",
            skills="Python, Testing"
        )
        self.assertIsNotNone(resume.resume_id)
        self.assertEqual(resume.full_name, "Тестовый Кандидат")
    
    def test_03_create_hr_profile(self):
        """Тест создания профиля HR"""
        hr = self.service.create_hr_profile(
            login="test_hr",
            password_hash="hash456",
            email="hr@test.com"
        )
        self.assertIsNotNone(hr.hr_id)
        self.assertEqual(hr.login, "test_hr")
    
    def test_04_create_hr_additional_info(self):
        """Тест создания доп. информации HR"""
        hr = self.service.get_hr_profile_by_login("test_hr")
        
        info = self.service.create_hr_additional_info(
            hr_id=hr.hr_id,
            full_name="Тестовый HR",
            position="HR Manager",
            contact_phone="+7-900-111-11-11",
            company_name="Test Company"
        )
        self.assertIsNotNone(info.id)
        self.assertEqual(info.full_name, "Тестовый HR")
    
    def test_05_create_vacancy(self):
        """Тест создания вакансии"""
        hr = self.service.get_hr_profile_by_login("test_hr")
        
        vacancy = self.service.create_vacancy(
            hr_id=hr.hr_id,
            position_title="Test Developer",
            job_description="Testing position",
            requirements="Python, Testing",
            questions="1. Test question?",
            status=VacancyStatus.OPEN
        )
        self.assertIsNotNone(vacancy.vacancy_id)
        self.assertEqual(vacancy.position_title, "Test Developer")
    
    def test_06_create_interview_stage1(self):
        """Тест создания первого этапа собеседования"""
        user = self.service.get_user_profile_by_login("test_candidate")
        hr = self.service.get_hr_profile_by_login("test_hr")
        vacancies = self.service.get_all_vacancies()
        
        interview = self.service.create_interview_stage1(
            user_id=user.user_id,
            hr_id=hr.hr_id,
            vacancy_id=vacancies[0].vacancy_id,
            interview_date=datetime.now(),
            questions="Test questions",
            candidate_answers="Test answers",
            video_recording_path="/test/video.mp4",
            soft_skills_score=85
        )
        self.assertIsNotNone(interview.interview1_id)
        self.assertEqual(interview.soft_skills_score, 85)
    
    def test_07_create_interview_stage2(self):
        """Тест создания второго этапа собеседования"""
        user = self.service.get_user_profile_by_login("test_candidate")
        hr = self.service.get_hr_profile_by_login("test_hr")
        vacancies = self.service.get_all_vacancies()
        
        # Получаем interview1_id из предыдущего теста
        session = self.service.db.get_session()
        try:
            interview1 = session.query(InterviewStage1).filter(
                InterviewStage1.user_id == user.user_id
            ).first()
            interview1_id = interview1.interview1_id
        finally:
            session.close()
        
        interview2 = self.service.create_interview_stage2(
            user_id=user.user_id,
            hr_id=hr.hr_id,
            interview1_id=interview1_id,
            vacancy_id=vacancies[0].vacancy_id,
            interview_date=datetime.now(),
            technical_tasks="Test task",
            candidate_solutions="Test solution",
            video_recording_path="/test/video2.mp4",
            hard_skills_score=90
        )
        self.assertIsNotNone(interview2.interview2_id)
        self.assertEqual(interview2.hard_skills_score, 90)
    
    def test_08_create_candidate_report(self):
        """Тест создания отчета"""
        user = self.service.get_user_profile_by_login("test_candidate")
        hr = self.service.get_hr_profile_by_login("test_hr")
        vacancies = self.service.get_all_vacancies()
        
        session = self.service.db.get_session()
        try:
            interview1 = session.query(InterviewStage1).filter(
                InterviewStage1.user_id == user.user_id
            ).first()
            interview2 = session.query(InterviewStage2).filter(
                InterviewStage2.user_id == user.user_id
            ).first()
        finally:
            session.close()
        
        final_score = (interview1.soft_skills_score + interview2.hard_skills_score) / 2
        
        report = self.service.create_candidate_report(
            user_id=user.user_id,
            hr_id=hr.hr_id,
            vacancy_id=vacancies[0].vacancy_id,
            interview1_id=interview1.interview1_id,
            interview2_id=interview2.interview2_id,
            final_score=final_score,
            hr_recommendations="Test recommendation"
        )
        self.assertIsNotNone(report.report_id)
        self.assertAlmostEqual(report.final_score, 87.5, places=1)
    
    def test_09_get_open_vacancies(self):
        """Тест получения открытых вакансий"""
        vacancies = self.service.get_open_vacancies()
        self.assertGreater(len(vacancies), 0)
    
    def test_10_delete_user_profile(self):
        """Тест удаления профиля кандидата"""
        # Создаем временного пользователя
        temp_user = self.service.create_user_profile(
            login="temp_user",
            password_hash="temp",
            email="temp@test.com"
        )
        user_id = temp_user.user_id
        
        result = self.service.delete_user_profile(user_id)
        self.assertTrue(result)
        
        deleted = self.service.get_user_profile_by_id(user_id)
        self.assertIsNone(deleted)


if __name__ == '__main__':
    unittest.main()
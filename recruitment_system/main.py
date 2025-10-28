from datetime import datetime, date
from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import (VacancyStatus)


def main():
    """Демонстрация работы системы рекрутинга Simple HR"""
    
    print("=" * 60)
    print("Simple HR - Демонстрация работы с БД")
    print("=" * 60)
    
    # Инициализация
    DATABASE_URL = 'sqlite:///simple_hr.db'
    db_repo = DatabaseRepository(DATABASE_URL)
    
    # Создаем таблицы
    print("\n1. Создание структуры БД...")
    db_repo.create_tables()
    print("   ✓ Таблицы созданы успешно")
    
    service = RecruitmentService(db_repo)
    
    # ========== СОЗДАНИЕ HR ==========
    print("\n2. Создание HR-менеджера...")
    hr = service.create_hr_profile(
        login="hr_maria",
        password_hash="hash_maria_123",
        email="maria@techcorp.com"
    )
    print(f"   ✓ HR создан: {hr.login} (ID: {hr.hr_id})")
    
    # Доп. информация HR
    hr_info = service.create_hr_additional_info(
        hr_id=hr.hr_id,
        full_name="Мария Ивановна Рекрутерова",
        position="Senior HR Manager",
        contact_phone="+7-999-888-77-66",
        company_name="TechCorp Solutions"
    )
    print(f"   ✓ Доп. информация HR: {hr_info.full_name}")
    
    # ========== СОЗДАНИЕ КАНДИДАТОВ ==========
    print("\n3. Создание кандидатов...")
    
    candidate1 = service.create_user_profile(
        login="alex_dev",
        password_hash="hash_alex_456",
        email="alex@email.com"
    )
    print(f"   ✓ Кандидат 1: {candidate1.login} (ID: {candidate1.user_id})")
    
    # Резюме кандидата 1
    resume1 = service.create_resume(
        user_id=candidate1.user_id,
        full_name="Александр Программистов",
        birth_date=date(1995, 5, 15),
        contact_phone="+7-900-111-22-33",
        contact_email="alex@email.com",
        education="МГУ, Факультет ВМК, 2017",
        work_experience="5 лет Python разработки в стартапах",
        skills="Python, FastAPI, Django, PostgreSQL, Docker, Git"
    )
    print(f"   ✓ Резюме создано: {resume1.full_name}")
    
    candidate2 = service.create_user_profile(
        login="maria_dev",
        password_hash="hash_maria_789",
        email="maria.dev@email.com"
    )
    print(f"   ✓ Кандидат 2: {candidate2.login} (ID: {candidate2.user_id})")
    
    resume2 = service.create_resume(
        user_id=candidate2.user_id,
        full_name="Мария Разработчикова",
        birth_date=date(1997, 8, 20),
        contact_phone="+7-900-333-44-55",
        contact_email="maria.dev@email.com",
        education="СПбГУ, Прикладная математика, 2019",
        work_experience="3 года Full-stack разработки",
        skills="Python, React, Node.js, MongoDB"
    )
    print(f"   ✓ Резюме создано: {resume2.full_name}")
    
    # ========== СОЗДАНИЕ ВАКАНСИЙ ==========
    print("\n4. Создание вакансий...")
    
    vacancy1 = service.create_vacancy(
        hr_id=hr.hr_id,
        position_title="Senior Python Developer",
        job_description="Разработка высоконагруженных систем на Python/FastAPI",
        requirements="Python 3.9+, FastAPI, PostgreSQL, Docker, 5+ лет опыта",
        questions="1. Расскажите о себе\n2. Опыт работы с FastAPI?\n3. Работали ли с микросервисами?",
        status=VacancyStatus.OPEN
    )
    print(f"   ✓ Вакансия: {vacancy1.position_title} (ID: {vacancy1.vacancy_id})")
    
    vacancy2 = service.create_vacancy(
        hr_id=hr.hr_id,
        position_title="Full-stack Developer",
        job_description="Разработка веб-приложений",
        requirements="Python, React, 3+ года опыта",
        questions="1. Расскажите о своих проектах\n2. Опыт работы с React?",
        status=VacancyStatus.OPEN
    )
    print(f"   ✓ Вакансия: {vacancy2.position_title} (ID: {vacancy2.vacancy_id})")
    
    # ========== ПРОВЕДЕНИЕ СОБЕСЕДОВАНИЙ ==========
    print("\n5. Проведение собеседований...")
    
    # Собеседование кандидата 1 - Этап 1
    interview1_stage1 = service.create_interview_stage1(
        user_id=candidate1.user_id,
        hr_id=hr.hr_id,
        vacancy_id=vacancy1.vacancy_id,
        interview_date=datetime.now(),
        questions=vacancy1.questions,
        candidate_answers="Я опытный Python разработчик с 5 летним стажем. Работал с FastAPI 2 года...",
        video_recording_path="/videos/alex_stage1.mp4",
        soft_skills_score=88
    )
    print(f"   ✓ Этап 1 ({candidate1.login}): Soft Skills = {interview1_stage1.soft_skills_score}/100")
    
    # Собеседование кандидата 1 - Этап 2
    interview1_stage2 = service.create_interview_stage2(
        user_id=candidate1.user_id,
        hr_id=hr.hr_id,
        interview1_id=interview1_stage1.interview1_id,
        vacancy_id=vacancy1.vacancy_id,
        interview_date=datetime.now(),
        technical_tasks="Реализовать REST API с JWT аутентификацией используя FastAPI",
        candidate_solutions="Код решения: app = FastAPI()... (полное решение)",
        video_recording_path="/videos/alex_stage2.mp4",
        hard_skills_score=92
    )
    print(f"   ✓ Этап 2 ({candidate1.login}): Hard Skills = {interview1_stage2.hard_skills_score}/100")
    
    # Собеседование кандидата 2 - Этап 1
    interview2_stage1 = service.create_interview_stage1(
        user_id=candidate2.user_id,
        hr_id=hr.hr_id,
        vacancy_id=vacancy2.vacancy_id,
        interview_date=datetime.now(),
        questions=vacancy2.questions,
        candidate_answers="Я Full-stack разработчик. Работала с React и Python...",
        video_recording_path="/videos/maria_stage1.mp4",
        soft_skills_score=85
    )
    print(f"   ✓ Этап 1 ({candidate2.login}): Soft Skills = {interview2_stage1.soft_skills_score}/100")
    
    interview2_stage2 = service.create_interview_stage2(
        user_id=candidate2.user_id,
        hr_id=hr.hr_id,
        interview1_id=interview2_stage1.interview1_id,
        vacancy_id=vacancy2.vacancy_id,
        interview_date=datetime.now(),
        technical_tasks="Создать React компонент с интеграцией backend API",
        candidate_solutions="React компонент с hooks и axios...",
        video_recording_path="/videos/maria_stage2.mp4",
        hard_skills_score=87
    )
    print(f"   ✓ Этап 2 ({candidate2.login}): Hard Skills = {interview2_stage2.hard_skills_score}/100")
    
    # ========== ГЕНЕРАЦИЯ ОТЧЕТОВ ==========
    print("\n6. Генерация отчетов по кандидатам...")
    
    # Отчет по кандидату 1
    final_score1 = (interview1_stage1.soft_skills_score + interview1_stage2.hard_skills_score) / 2
    report1 = service.create_candidate_report(
        user_id=candidate1.user_id,
        hr_id=hr.hr_id,
        vacancy_id=vacancy1.vacancy_id,
        interview1_id=interview1_stage1.interview1_id,
        interview2_id=interview1_stage2.interview2_id,
        final_score=final_score1,
        hr_recommendations=f"РЕКОМЕНДУЕТСЯ К НАЙМУ.\n\n"
                        f"Кандидат: {resume1.full_name}\n"
                        f"Вакансия: {vacancy1.position_title}\n\n"
                        f"Soft Skills: {interview1_stage1.soft_skills_score}/100\n"
                        f"Hard Skills: {interview1_stage2.hard_skills_score}/100\n"
                        f"Итоговая оценка: {final_score1}/100\n\n"
                        f"Отличные технические навыки и опыт работы с FastAPI."
    )
    print(f"   ✓ Отчет создан для {resume1.full_name}: {report1.final_score}/100")
    
    # Отчет по кандидату 2
    final_score2 = (interview2_stage1.soft_skills_score + interview2_stage2.hard_skills_score) / 2
    report2 = service.create_candidate_report(
        user_id=candidate2.user_id,
        hr_id=hr.hr_id,
        vacancy_id=vacancy2.vacancy_id,
        interview1_id=interview2_stage1.interview1_id,
        interview2_id=interview2_stage2.interview2_id,
        final_score=final_score2,
        hr_recommendations=f"РЕКОМЕНДУЕТСЯ К НАЙМУ.\n\n"
                        f"Кандидат: {resume2.full_name}\n"
                        f"Вакансия: {vacancy2.position_title}\n\n"
                        f"Soft Skills: {interview2_stage1.soft_skills_score}/100\n"
                        f"Hard Skills: {interview2_stage2.hard_skills_score}/100\n"
                        f"Итоговая оценка: {final_score2}/100\n\n"
                        f"Хорошие навыки Full-stack разработки."
    )
    print(f"   ✓ Отчет создан для {resume2.full_name}: {report2.final_score}/100")
    
    # ========== СТАТИСТИКА ==========
    print("\n7. Статистика системы:")
    all_users = service.get_all_user_profiles()
    all_vacancies = service.get_all_vacancies()
    open_vacancies = service.get_open_vacancies()
    
    print(f"   • Всего кандидатов: {len(all_users)}")
    print(f"   • Всего вакансий: {len(all_vacancies)}")
    print(f"   • Открытых вакансий: {len(open_vacancies)}")
    
    print("\n" + "=" * 60)
    print("Демонстрация завершена успешно!")
    print("=" * 60)
    print(f"\nБаза данных: simple_hr.db")


if __name__ == "__main__":
    main()

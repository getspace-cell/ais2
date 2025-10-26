# Главный файл приложения для демонстрации работы

from datetime import datetime, date
from repository import DatabaseRepository
from services.repository_service import RecruitmentService
from models.dao import (
    User, UserRole, HRProfile, Resume, Vacancy, 
    VacancyStatus, InterviewStage1, InterviewStage2, 
    CandidateReport
)
import sys, os


def main():
    """Демонстрация работы системы рекрутинга"""
    
    # Инициализация БД (для локального тестирования используем SQLite)
    print("=" * 60)
    print("Система рекрутинга - Демонстрация работы с БД")
    print("=" * 60)
    
    # Для локального тестирования
    DATABASE_URL = 'sqlite:///recruitment.db'
    
    # Для подключения к MariaDB раскомментируйте:
    # DATABASE_URL = 'mysql+pymysql://usr:qwerty@192.168.56.104/recruitment_db?charset=utf8'
    
    db_repo = DatabaseRepository(DATABASE_URL)
    
    # Создаем таблицы
    print("\n1. Создание структуры БД...")
    if os.path.exists("/Users/ruslan/Desktop/ais2/recruitment.db"):
        print('бд уже заполнена')
        sys.exit()
        
    else:
        db_repo.create_tables()
        print("   ✓ Таблицы созданы успешно")

    
    # Инициализируем сервис
    service = RecruitmentService(db_repo)
    
    # Создаем HR-менеджера
    print("\n2. Создание HR-менеджера...")
    hr_user = service.create_user(
        login="hr_manager",
        password_hash="secure_hash_123",
        email="hr@techcorp.com",
        full_name="Сидоров Петр Иванович",
        role=UserRole.HR
    )
    print(f"   ✓ HR создан: {hr_user.full_name} (ID: {hr_user.user_id})")
    
    # Создаем профиль HR
    session = db_repo.get_session()
    try:
        hr_profile = HRProfile(
            user_id=hr_user.user_id,
            full_name=hr_user.full_name,
            position="Senior HR Manager",
            contact_phone="+7-999-888-77-66",
            company_name="TechCorp Solutions"
        )
        session.add(hr_profile)
        session.commit()
        session.refresh(hr_profile)
        print(f"   ✓ HR профиль создан (ID: {hr_profile.hr_id})")
    finally:
        session.close()
    
    # Создаем кандидатов
    print("\n3. Создание кандидатов...")
    candidate1 = service.create_user(
        login="dev_alice",
        password_hash="hash_456",
        email="alice@example.com",
        full_name="Алиса Разработкина",
        role=UserRole.CANDIDATE
    )
    print(f"   ✓ Кандидат 1: {candidate1.full_name}")
    
    candidate2 = service.create_user(
        login="dev_bob",
        password_hash="hash_789",
        email="bob@example.com",
        full_name="Боб Программистов",
        role=UserRole.CANDIDATE
    )
    print(f"   ✓ Кандидат 2: {candidate2.full_name}")
    
    # Создаем резюме для кандидатов
    session = db_repo.get_session()
    try:
        resume1 = Resume(
            user_id=candidate1.user_id,
            birth_date=date(1995, 5, 15),
            contact_phone="+7-900-111-22-33",
            contact_email=candidate1.email,
            education="МГУ, Факультет ВМК, 2017",
            work_experience="5 лет Python разработки",
            skills="Python, Django, PostgreSQL, Docker"
        )
        session.add(resume1)
        session.commit()
        print(f"   ✓ Резюме создано для {candidate1.full_name}")
    finally:
        session.close()
    
    # Создаем вакансии
    print("\n4. Создание вакансий...")
    vacancy1 = service.create_vacancy(
        hr_id=hr_profile.hr_id,
        position_title="Senior Python Developer",
        job_description="Разработка высоконагруженных систем на Python",
        requirements="Python 3.9+, FastAPI, PostgreSQL, 5+ лет опыта"
    )
    print(f"   ✓ Вакансия: {vacancy1.position_title} (ID: {vacancy1.vacancy_id})")
    
    vacancy2 = service.create_vacancy(
        hr_id=hr_profile.hr_id,
        position_title="Junior Python Developer",
        job_description="Разработка веб-приложений",
        requirements="Python 3.x, Django/Flask, 1+ год опыта"
    )
    print(f"   ✓ Вакансия: {vacancy2.position_title} (ID: {vacancy2.vacancy_id})")
    
    # Создаем собеседования
    print("\n5. Проведение собеседований...")
    interview1_stage1 = service.create_interview_stage1(
        user_id=candidate1.user_id,
        hr_id=hr_profile.hr_id,
        vacancy_id=vacancy1.vacancy_id,
        interview_date=datetime.now(),
        questions="1. Расскажите о себе\n2. Почему выбрали нашу компанию?\n3. Ваши сильные стороны?",
        candidate_answers="Я опытный разработчик с 5 летним стажем...",
        soft_skills_score=92,
        confidence_score=88
    )
    print(f"   ✓ Этап 1 для {candidate1.full_name}: Soft Skills={interview1_stage1.soft_skills_score}")
    
    interview1_stage2 = service.create_interview_stage2(
        user_id=candidate1.user_id,
        hr_id=hr_profile.hr_id,
        interview1_id=interview1_stage1.interview1_id,
        vacancy_id=vacancy1.vacancy_id,
        interview_date=datetime.now(),
        technical_tasks="Реализовать REST API с аутентификацией",
        candidate_solutions="Решение реализовано с использованием FastAPI и JWT...",
        hard_skills_score=95,
        final_result="Принят"
    )
    print(f"   ✓ Этап 2 для {candidate1.full_name}: Hard Skills={interview1_stage2.hard_skills_score}, Результат={interview1_stage2.final_result}")
    
    # Создаем отчет
    print("\n6. Генерация отчета по кандидату...")
    final_score = (interview1_stage1.soft_skills_score + interview1_stage2.hard_skills_score) / 2
    report = service.create_candidate_report(
        user_id=candidate1.user_id,
        hr_id=hr_profile.hr_id,
        vacancy_id=vacancy1.vacancy_id,
        interview1_id=interview1_stage1.interview1_id,
        interview2_id=interview1_stage2.interview2_id,
        final_score=final_score,
        hr_recommendations=f"РЕКОМЕНДУЕТСЯ К НАЙМУ.\n\nКандидат показал отличные результаты на обоих этапах собеседования.\nSoft skills: {interview1_stage1.soft_skills_score}/100\nHard skills: {interview1_stage2.hard_skills_score}/100\nИтоговая оценка: {final_score}/100"
    )
    print(f"   ✓ Отчет создан (ID: {report.report_id})")
    print(f"   ✓ Итоговая оценка: {report.final_score}/100")
    
    # Статистика
    print("\n7. Статистика системы:")
    all_users = service.get_all_users()
    hr_users = service.get_all_users(role=UserRole.HR)
    candidates = service.get_all_users(role=UserRole.CANDIDATE)
    open_vacancies = service.get_open_vacancies()
    
    print(f"   • Всего пользователей: {len(all_users)}")
    print(f"   • HR-менеджеров: {len(hr_users)}")
    print(f"   • Кандидатов: {len(candidates)}")
    print(f"   • Открытых вакансий: {len(open_vacancies)}")
    
    print("\n" + "=" * 60)
    print("Демонстрация завершена успешно!")
    print("=" * 60)
    print(f"\nБаза данных сохранена в файле: recruitment.db")
    print("Для подключения к MariaDB измените DATABASE_URL в main()")


if __name__ == "__main__":
    main()
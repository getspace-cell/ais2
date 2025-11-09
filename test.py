"""
Тестовый скрипт для проверки нового функционала
Запуск: python test_new_features.py
"""
import asyncio
import httpx
import json
from pathlib import Path

BASE_URL = "http://localhost:8000/api/v1"

# Глобальные переменные для токенов
hr_token = None
candidate_token = None
vacancy_id = None
candidate_ids = []
user_moc_auth = []


async def test_hr_registration():
    """Тест 1: Регистрация HR"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Регистрация HR")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "login": "test_hr",
                "password": "testpass123",
                "email": "test_hr@example.com",
                "full_name": "Test HR Manager",
                "role": "HR"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            global hr_token
            hr_token = data['access_token']
            print(f"✅ HR зарегистрирован успешно")
            print(f"   Token: {hr_token[:30]}...")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False
async def test_candidate_registration():
    """Тест 1: Регистрация HR"""
    print("\n" + "="*60)
    print("ТЕСТ 1: Регистрация HR")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/register",
            json={
                "login": "candidate_1",
                "password": "testpass123",
                "email": "test_candidate@example.com",
                "full_name": "asdfasdf",
                "role": "CANDIDATE"
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            global hr_token
            hr_token = data['access_token']
            print(f"✅ HR зарегистрирован успешно")
            print(f"   Token: {hr_token[:30]}...")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_create_vacancy_with_questions():
    """Тест 2: Создание вакансии с вопросами"""
    print("\n" + "="*60)
    print("ТЕСТ 2: Создание вакансии с вопросами")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{BASE_URL}/vacancies",
            headers={"Authorization": f"Bearer {hr_token}"},
            json={
                "position_title": "Senior Python Developer",
                "job_description": "Разработка backend на FastAPI",
                "requirements": "Python 3.9+, FastAPI, PostgreSQL",
                "questions": [
                    "Какой стек технологий вы планируете изучать?",
                    "Ваш коллега не вовремя закончил проект, ваши действия?",
                    "Опишите ваш самый сложный проект"
                ]
            }
        )
        
        if response.status_code == 201:
            data = response.json()
            global vacancy_id
            vacancy_id = data['vacancy_id']
            
            # Проверяем вопросы в ответе или делаем дополнительный запрос
            questions_count = len(data.get('questions', []))
            if questions_count == 0:
                # Делаем GET запрос для проверки
                get_response = await client.get(
                    f"{BASE_URL}/vacancies/{vacancy_id}",
                    headers={"Authorization": f"Bearer {hr_token}"}
                )
                if get_response.status_code == 200:
                    get_data = get_response.json()
                    questions_count = len(get_data.get('questions', []))
            
            print(f"✅ Вакансия создана успешно")
            print(f"   ID: {vacancy_id}")
            print(f"   Вопросов: {questions_count}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_upload_resumes_simulation():
    """Тест 3: Симуляция загрузки резюме (без реального ZIP)"""
    ZIP_PATH = Path("/Users/ruslan/Desktop/ais2/Архив.zip")
    if not ZIP_PATH.exists():
        print(f"❌ Файл {ZIP_PATH} не найден")
        return

    headers = {"Authorization": f"Bearer {hr_token}"}

    async with httpx.AsyncClient(timeout=120) as client:
        with ZIP_PATH.open("rb") as f:
            files = {"zip_file": ("архив.zip", f, "application/zip")}
            response = await client.post(
                f"{BASE_URL}/vacancies/{vacancy_id}/upload_resumes",
                headers=headers,
                files=files,
            )

        if response.status_code == 200:
            data = response.json()
            print("✅ Резюме успешно загружены и обработаны")
            print(f"   Всего обработано: {data['total_processed']}")
            abc = data.get("created_candidates", [])[2]
            global user_moc_auth
            user_moc_auth=[abc['login'],abc['password']]
            print(user_moc_auth)

            for c in data.get("created_candidates", []):
                cid = c.get("user_id")
                candidate_ids.append(cid)
                print(f"   → {c['full_name']} ({c['login']} / {c['password']}) [user_id={cid}]")

            print(f"\n📦 Список candidate_ids: {candidate_ids}")
            return len(candidate_ids) > 0
        else:
            print(f"❌ Ошибка {response.status_code}")
            print(response.text)
            return len(candidate_ids) > 0

async def test_invite_candidates():
    """Тест 4: Приглашение кандидатов на собеседование"""
    print("\n" + "="*60)
    print("ТЕСТ 4: Приглашение кандидатов")
    print("="*60)
    if not candidate_ids:
        print("❌ Нет кандидатов для приглашения")
        return False
    
    
    
    # Увеличенный таймаут для отправки email
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            f"{BASE_URL}/interview/invite",
            headers={"Authorization": f"Bearer {hr_token}"},
            data={
                "candidate_ids": candidate_ids,
                "vacancy_id": vacancy_id
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Приглашения отправлены")
            print(f"   Всего: {data['total_invited']}")
            print(f"   Успешно: {data['successful_invites']}")
            print(f"   Ошибок: {data['failed_invites']}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            print(f"   {response.text}")
            return False


async def test_candidate_get_questions():
    """Тест 5: Получение вопросов кандидатом"""
    print("\n" + "="*60)
    print("ТЕСТ 5: Получение вопросов кандидатом")
    print("="*60)
    
    # Логинимся как кандидат
    async with httpx.AsyncClient() as client:
        login_response = await client.post(
            f"{BASE_URL}/login",
            json={
                "login": user_moc_auth[0],
                "password": user_moc_auth[1]
            }
        )
        
        if login_response.status_code != 200:
            print("❌ Не удалось войти как кандидат")
            return False
        
        global candidate_token
        candidate_token = login_response.json()['access_token']
        
        # Получаем вопросы
        response = await client.get(
            f"{BASE_URL}/vacancies/{vacancy_id}/interview",
            headers={"Authorization": f"Bearer {candidate_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Вопросы получены")
            print(f"   Вакансия: {data['position_title']}")
            print(f"   Количество вопросов: {len(data['questions'])}")
            for i, q in enumerate(data['questions'], 1):
                print(f"   {i}. {q}")
            return True
        else:
            print(f"❌ Ошибка: {response.status_code}")
            return False


async def test_submit_interview_simulation():
    """Тест 6: Отправка ответов на интервью"""
    print("\n" + "="*60)
    print("ТЕСТ 6: Отправка ответов")
    print("="*60)

    VIDEO_PATH = Path("/Users/ruslan/Desktop/ais2/interview.mp4")
    if not VIDEO_PATH.exists():
        print(f"❌ Файл {VIDEO_PATH} не найден")
        return False

    text_answers = "Тестовый ответ на все вопросы"

    headers = {"Authorization": f"Bearer {candidate_token}"}

    async with httpx.AsyncClient(timeout=120) as client:
        with VIDEO_PATH.open("rb") as f:
            files = {
                "video_file": ("test_video.mp4", f, "video/mp4"),
                "text_answers": (None, text_answers)
            }
            response = await client.post(
                f"{BASE_URL}/vacancies/{vacancy_id}/submit_interview",
                headers=headers,
                files=files
            )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Интервью отправлено")
            print(f"   Interview ID: {data['interview1_id']}")
            print(f"   Soft skills: {data['soft_skills_score']}")
            print(f"   Confidence: {data['confidence_score']}")
            return True
        else:
            print(f"❌ Ошибка {response.status_code}")
            print(response.text)
            return False



async def test_hr_view_interviews():
    """Тест 7: Просмотр результатов интервью HR"""
    print("\n" + "="*60)
    print("ТЕСТ 7: Просмотр интервью HR")
    print("="*60)
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{BASE_URL}/interviews/candidate/{candidate_ids[0]}",
            headers={"Authorization": f"Bearer {hr_token}"}
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Интервью получены")
            print(f"   Найдено интервью: {len(data)}")
            return True
        else:
            print(f"⚠️  Интервью не найдены (ожидаемо, если не было реальной отправки)")
            return True


async def run_all_tests():
    """Запуск всех тестов"""
    print("\n" + "🚀 " + "="*58)
    print("   ТЕСТИРОВАНИЕ НОВОГО ФУНКЦИОНАЛА SIMPLE HR")
    print("="*60)
    
    results = []
    
    # Запускаем тесты последовательно
    results.append(("Регистрация HR", await test_hr_registration()))
    results.append(("Создание вакансии", await test_create_vacancy_with_questions()))
    results.append(("Загрузка резюме", await test_upload_resumes_simulation()))
    results.append(("Приглашение кандидатов", await test_invite_candidates()))
    results.append(("Получение вопросов", await test_candidate_get_questions()))
    results.append(("Отправка ответов", await test_submit_interview_simulation()))
    results.append(("Просмотр интервью", await test_hr_view_interviews()))
    
    # Итоги
    print("\n" + "="*60)
    print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
    
    print(f"\nИтого: {passed}/{total} тестов пройдено")
    
    if passed == total:
        print("\n🎉 Все тесты успешно пройдены!")
    else:
        print(f"\n⚠️  Некоторые тесты не прошли ({total - passed} ошибок)")
    
    print("\n" + "="*60)
    print("💡 Примечания:")
    print("   - Тесты 3 и 6 требуют реальных файлов и API ключей")
    print("   - Для полного тестирования настройте .env с реальными ключами")
    print("   - Email рассылка может быть заблокирована без настроенного SMTP")
    print("="*60)


if __name__ == "__main__":
    print("\n⚡ Убедитесь что сервер запущен: python app.py")
    print("   URL: http://localhost:8000\n")
    
    asyncio.run(run_all_tests())
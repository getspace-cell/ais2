

from locust import HttpUser, task, between, tag
import random
import json

HR_CREDENTIALS = {
    "login": "hr_test",
    "password": "test123"
}

CANDIDATE_CREDENTIALS = {
    "login": "candidate_test", 
    "password": "test123"
}

VACANCY_DATA = {
    "position_title": "Python Developer",
    "job_description": "Разработка backend на FastAPI",
    "requirements": "Python 3.9+, FastAPI, PostgreSQL",
    "questions": ["Расскажите о себе", "Опыт работы с FastAPI?"]
}

RESUME_DATA = {
    "birth_date": "1995-05-15",
    "contact_phone": "+7-900-123-45-67",
    "contact_email": "test@email.com",
    "education": "МГУ, ВМК, 2017",
    "work_experience": "5 лет Python",
    "skills": "Python, FastAPI, PostgreSQL"
}


class SimpleHRUser(HttpUser):
    """
    Класс для эмуляции пользователя системы Simple HR.
    Имитирует действия как HR, так и кандидатов.
    """
    
    # Время ожидания между задачами (1-3 секунды)
    wait_time = between(1.0, 3.0)
    
    # Токены для авторизованных запросов
    hr_token = None
    candidate_token = None
    
    def on_start(self):
        """
        Выполняется при запуске пользователя.
        Регистрируем тестовых пользователей если их нет.
        """
        # Пытаемся войти как HR
        self.login_as_hr()
        
        # Пытаемся войти как кандидат
        self.login_as_candidate()
    
    def login_as_hr(self):
        """Вход в систему как HR"""
        response = self.client.post(
            "/api/v1/login",
            json=HR_CREDENTIALS,
            catch_response=True,
            name="[AUTH] Login as HR"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.hr_token = data['access_token']
            response.success()
        elif response.status_code == 401:
            # Пробуем зарегистрироваться
            self.register_hr()
        else:
            response.failure(f"Login failed: {response.status_code}")
    
    def login_as_candidate(self):
        """Вход в систему как кандидат"""
        response = self.client.post(
            "/api/v1/login",
            json=CANDIDATE_CREDENTIALS,
            catch_response=True,
            name="[AUTH] Login as Candidate"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.candidate_token = data['access_token']
            response.success()
        elif response.status_code == 401:
            # Пробуем зарегистрироваться
            self.register_candidate()
        else:
            response.failure(f"Login failed: {response.status_code}")
    
    def register_hr(self):
        """Регистрация HR"""
        register_data = {
            "login": HR_CREDENTIALS["login"],
            "password": HR_CREDENTIALS["password"],
            "email": f"{HR_CREDENTIALS['login']}@test.com",
            "full_name": "Test HR Manager",
            "role": "HR"
        }
        
        response = self.client.post(
            "/api/v1/register",
            json=register_data,
            catch_response=True,
            name="[AUTH] Register HR"
        )
        
        if response.status_code == 201:
            data = response.json()
            self.hr_token = data['access_token']
            response.success()
        else:
            response.failure(f"Registration failed: {response.status_code}")
    
    def register_candidate(self):
        """Регистрация кандидата"""
        register_data = {
            "login": CANDIDATE_CREDENTIALS["login"],
            "password": CANDIDATE_CREDENTIALS["password"],
            "email": f"{CANDIDATE_CREDENTIALS['login']}@test.com",
            "full_name": "Test Candidate",
            "role": "Кандидат"
        }
        
        response = self.client.post(
            "/api/v1/register",
            json=register_data,
            catch_response=True,
            name="[AUTH] Register Candidate"
        )
        
        if response.status_code == 201:
            data = response.json()
            self.candidate_token = data['access_token']
            response.success()
        else:
            response.failure(f"Registration failed: {response.status_code}")
    
    # ========== GET запросы (легкие) ==========
    
    @tag("get_light")
    @task(5)
    def get_all_vacancies(self):
        """GET: Получение всех вакансий"""
        if not self.candidate_token:
            return
        
        with self.client.get(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            catch_response=True,
            name="[GET] Get all vacancies"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("get_light")
    @task(3)
    def get_my_profile(self):
        """GET: Получение своего профиля"""
        if not self.candidate_token:
            return
        
        with self.client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            catch_response=True,
            name="[GET] Get my profile"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("get_light")
    @task(2)
    def get_statistics(self):
        """GET: Получение статистики (только HR)"""
        if not self.hr_token:
            return
        
        with self.client.get(
            "/api/v1/statistics/overview",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            catch_response=True,
            name="[GET] Get statistics"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    # ========== POST запросы (тяжелые) ==========
    
    @tag("post_heavy")
    @task(2)
    def create_vacancy(self):
        """POST: Создание вакансии (HR)"""
        if not self.hr_token:
            return
        
        # Добавляем случайность к названию
        vacancy_data = VACANCY_DATA.copy()
        vacancy_data["position_title"] = f"{VACANCY_DATA['position_title']} #{random.randint(1, 1000)}"
        
        with self.client.post(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            json=vacancy_data,
            catch_response=True,
            name="[POST] Create vacancy"
        ) as response:
            if response.status_code == 201:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("post_heavy")
    @task(1)
    def create_resume(self):
        """POST: Создание резюме (Кандидат)"""
        if not self.candidate_token:
            return
        
        with self.client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            json=RESUME_DATA,
            catch_response=True,
            name="[POST] Create resume"
        ) as response:
            if response.status_code in [201, 400]:  # 400 если уже существует
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    # ========== PUT запросы (средние) ==========
    
    @tag("put_medium")
    @task(2)
    def update_resume(self):
        """PUT: Обновление резюме"""
        if not self.candidate_token:
            return
        
        update_data = {
            "skills": f"Python, FastAPI, PostgreSQL, Docker (updated {random.randint(1, 100)})"
        }
        
        with self.client.put(
            "/api/v1/resumes/my",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            json=update_data,
            catch_response=True,
            name="[PUT] Update resume"
        ) as response:
            if response.status_code in [200, 404]:  # 404 если еще не создано
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    
    @tag("complex")
    @task(1)
    def hr_workflow(self):
        """
        Комплексный сценарий HR:
        1. Получить список всех пользователей
        2. Получить свои вакансии
        3. Получить статистику
        """
        if not self.hr_token:
            return
        
        headers = {"Authorization": f"Bearer {self.hr_token}"}
        
        # 1. Список пользователей
        with self.client.get(
            "/api/v1/users",
            headers=headers,
            catch_response=True,
            name="[WORKFLOW] HR - Get users"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
                return
        
        # 2. Список вакансий
        with self.client.get(
            "/api/v1/vacancies",
            headers=headers,
            catch_response=True,
            name="[WORKFLOW] HR - Get vacancies"
        ) as response:
            if response.status_code != 200:
                response.failure(f"Status: {response.status_code}")
                return
        
        # 3. Статистика
        with self.client.get(
            "/api/v1/statistics/overview",
            headers=headers,
            catch_response=True,
            name="[WORKFLOW] HR - Get stats"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")



class HROnlyUser(HttpUser):
    """Эмулирует только действия HR"""
    wait_time = between(1.0, 2.0)
    hr_token = None
    
    def on_start(self):
        """Вход как HR"""
        response = self.client.post("/api/v1/login", json=HR_CREDENTIALS)
        if response.status_code == 200:
            self.hr_token = response.json()['access_token']
    
    @task
    def hr_operations(self):
        """Операции HR"""
        if not self.hr_token:
            return
        
        headers = {"Authorization": f"Bearer {self.hr_token}"}
        
        # Случайный выбор операции
        operations = [
            ("/api/v1/users", "GET"),
            ("/api/v1/vacancies", "GET"),
            ("/api/v1/statistics/overview", "GET"),
        ]
        
        endpoint, method = random.choice(operations)
        
        if method == "GET":
            self.client.get(endpoint, headers=headers)


class CandidateOnlyUser(HttpUser):
    """Эмулирует только действия кандидата"""
    wait_time = between(1.0, 2.0)
    candidate_token = None
    
    def on_start(self):
        """Вход как кандидат"""
        response = self.client.post("/api/v1/login", json=CANDIDATE_CREDENTIALS)
        if response.status_code == 200:
            self.candidate_token = response.json()['access_token']
    
    @task
    def candidate_operations(self):
        """Операции кандидата"""
        if not self.candidate_token:
            return
        
        headers = {"Authorization": f"Bearer {self.candidate_token}"}
        
        # Случайный выбор операции
        operations = [
            ("/api/v1/vacancies", "GET"),
            ("/api/v1/me", "GET"),
            ("/api/v1/resumes/my", "GET"),
        ]
        
        endpoint, method = random.choice(operations)
        self.client.get(endpoint, headers=headers)


"""
=== ИНСТРУКЦИЯ ПО ЗАПУСКУ ===

1. Базовый запуск (с веб-интерфейсом):
   locust -f locust_test.py --host=http://localhost:8000
   
   Затем открыть: http://localhost:8089
   
2. Запуск в headless режиме (для автоматического тестирования):
   locust -f locust_test.py --host=http://localhost:8000 \
          --users 50 --spawn-rate 5 --run-time 3m --headless

3. Запуск только GET запросов:
   locust -f locust_test.py --host=http://localhost:8000 \
          --tags get_light

4. Запуск только POST запросов:
   locust -f locust_test.py --host=http://localhost:8000 \
          --tags post_heavy

5. Запуск только HR операций:
   locust -f locust_test.py --host=http://localhost:8000 \
          HROnlyUser

=== РЕКОМЕНДАЦИИ ПО ТЕСТИРОВАНИЮ ===

Этап 1 (Нагрузочное тестирование - GET+PUT):
- Запустить с тегами: --tags get_light put_medium
- Пользователи: 30-50
- Spawn rate: 5
- Длительность: 5 минут
- Цель: нагрузка CPU < 60%

Этап 2 (Объемное тестирование - добавляем POST):
- Запустить с тегами: --tags get_light post_heavy put_medium
- Пользователи: 50-70
- Spawn rate: 10
- Длительность: 5 минут
- Цель: проверка работы с растущей БД

Этап 3 (Стрессовое тестирование):
- Запустить все задачи без фильтров
- Пользователи: 100-200 (постепенно увеличивать)
- Spawn rate: 10-20
- Длительность: 10 минут
- Цель: CPU 90-100%, отказы < 1%

"""
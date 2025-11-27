"""
Сценарии нагрузочного тестирования для Simple HR API
Лабораторная работа №4 - ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

from locust import HttpUser, task, between, tag
import random
import json
import time
from datetime import datetime


# Тестовые данные с более уникальными идентификаторами
def get_test_users():
    timestamp = int(time.time())
    random_suffix = random.randint(10000, 99999)
    
    return {
        "hr": {
            "login": f"hr_load_{timestamp}_{random_suffix}",
            "password": "testpass123",
            "email": f"hr_{timestamp}_{random_suffix}@test.com",
            "full_name": f"Test HR Load {timestamp}",
            "role": "HR"
        },
        "candidate": {
            "login": f"candidate_load_{timestamp}_{random_suffix}",
            "password": "testpass123", 
            "email": f"candidate_{timestamp}_{random_suffix}@test.com",
            "full_name": f"Test Candidate Load {timestamp}",
            "role": "Кандидат"
        }
    }

VACANCY_TITLES = [
    "Python Developer",
    "Full-stack Developer", 
    "Backend Developer",
    "Frontend Developer",
    "DevOps Engineer",
    "Data Scientist",
    "ML Engineer",
    "QA Engineer",
    "System Administrator",
    "Product Manager"
]

VACANCY_DESCRIPTIONS = [
    "Мы ищем опытного разработчика для работы над высоконагруженным проектом",
    "Присоединяйтесь к нашей команде для разработки инновационных решений",
    "Работа над интересными задачами в дружном коллективе",
    "Возможность профессионального роста и реализации амбициозных проектов",
    "Разработка и поддержка бизнес-критичных приложений"
]


class SimpleHRUser(HttpUser):
    """
    Улучшенный класс для нагрузочного тестирования Simple HR системы.
    Решены проблемы с порядком выполнения операций и управлением состоянием.
    """
    
    wait_time = between(1.0, 3.0)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reset_state()
    
    def _reset_state(self):
        """Сброс состояния пользователя"""
        self.hr_token = None
        self.candidate_token = None
        self.hr_user_id = None
        self.candidate_user_id = None
        self.my_vacancies = []  # Только вакансии этого пользователя
        self.available_vacancies = []  # Все доступные вакансии
        self.initialized = False
    
    def on_start(self):
        """Надежная инициализация пользователя"""
        self._reset_state()
        test_users = get_test_users()
        
        # Регистрация HR с повторными попытками
        if self._register_user(test_users["hr"], "hr"):
            # Создаем минимум одну вакансию для HR
            self._create_initial_vacancy()
        
        # Регистрация кандидата
        self._register_user(test_users["candidate"], "candidate")
        
        self.initialized = self.hr_token or self.candidate_token
        
        if self.initialized:
            # Предварительная загрузка доступных вакансий
            self._refresh_available_vacancies()
    
    def _register_user(self, user_data, user_type):
        """Регистрация пользователя с обработкой ошибок"""
        max_attempts = 2
        for attempt in range(max_attempts):
            try:
                # Генерируем уникальные данные для каждой попытки
                unique_suffix = f"{int(time.time())}_{random.randint(1000, 9999)}"
                user_data_copy = user_data.copy()
                user_data_copy["login"] = f"{user_data['login']}_{unique_suffix}"
                user_data_copy["email"] = f"{user_data['email'].split('@')[0]}_{unique_suffix}@test.com"
                
                with self.client.post(
                    "/api/v1/register",
                    json=user_data_copy,
                    catch_response=True,
                    name=f"POST /api/v1/register ({user_type})"
                ) as response:
                    if response.status_code in [200, 201]:
                        data = response.json()
                        if user_type == "hr":
                            self.hr_token = data["access_token"]
                            self.hr_user_id = data["user_id"]
                        else:
                            self.candidate_token = data["access_token"] 
                            self.candidate_user_id = data["user_id"]
                        response.success()
                        return True
                    elif response.status_code == 400 and "уже существует" in response.text:
                        # Пробуем войти вместо регистрации
                        return self._login_user(user_data_copy, user_type)
                    else:
                        response.failure(f"{user_type} registration failed: {response.status_code}")
                        if attempt == max_attempts - 1:
                            return False
            except Exception as e:
                if attempt == max_attempts - 1:
                    return False
        return False
    
    def _login_user(self, user_data, user_type):
        """Вход для существующего пользователя"""
        login_data = {
            "login": user_data["login"],
            "password": user_data["password"]
        }
        
        with self.client.post(
            "/api/v1/login",
            json=login_data,
            catch_response=True,
            name=f"POST /api/v1/login ({user_type})"
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if user_type == "hr":
                    self.hr_token = data["access_token"]
                    self.hr_user_id = data["user_id"]
                else:
                    self.candidate_token = data["access_token"]
                    self.candidate_user_id = data["user_id"]
                response.success()
                return True
            else:
                response.failure(f"{user_type} login failed: {response.status_code}")
                return False
    
    def _create_initial_vacancy(self):
        """Создание начальной вакансии для HR"""
        if not self.hr_token:
            return
            
        vacancy_data = {
            "position_title": random.choice(VACANCY_TITLES),
            "job_description": random.choice(VACANCY_DESCRIPTIONS),
            "requirements": "Python 3.8+, опыт работы от 2 лет, знание SQL",
            "questions": [
                "Расскажите о вашем опыте работы с Python",
                "Какие фреймворки вы использовали?",
                "Почему хотите работать в нашей компании?"
            ]
        }
        
        with self.client.post(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            json=vacancy_data,
            catch_response=True,
            name="INITIAL: POST /api/v1/vacancies"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.my_vacancies.append(data["vacancy_id"])
                response.success()
    
    def _refresh_available_vacancies(self):
        """Обновление списка доступных вакансий"""
        token = self.candidate_token or self.hr_token
        if not token:
            return
            
        with self.client.get(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {token}"},
            catch_response=True,
            name="REFRESH: GET /api/v1/vacancies"
        ) as response:
            if response.status_code == 200:
                vacancies = response.json()
                self.available_vacancies = [v["vacancy_id"] for v in vacancies if v["vacancy_id"]]
                response.success()
    
    def _get_random_my_vacancy(self):
        """Получить случайную вакансию пользователя или создать новую"""
        if self.my_vacancies:
            return random.choice(self.my_vacancies)
        elif self.hr_token:
            # Создаем новую вакансию, если нет своих
            return self._create_vacancy_sync()
        return None
    
    def _create_vacancy_sync(self):
        """Синхронное создание вакансии с возвратом ID"""
        vacancy_data = {
            "position_title": random.choice(VACANCY_TITLES),
            "job_description": random.choice(VACANCY_DESCRIPTIONS),
            "requirements": "Базовые требования для нагрузочного тестирования",
            "questions": ["Вопрос 1?", "Вопрос 2?"]
        }
        
        response = self.client.post(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            json=vacancy_data
        )
        
        if response.status_code == 201:
            vacancy_id = response.json()["vacancy_id"]
            self.my_vacancies.append(vacancy_id)
            return vacancy_id
        return None
    
    def _ensure_has_vacancies(self):
        """Убедиться, что есть вакансии для операций"""
        if not self.available_vacancies:
            self._refresh_available_vacancies()
        return len(self.available_vacancies) > 0

    # ========== ЛЕГКИЕ GET ЗАПРОСЫ ==========
    
    @tag("get", "light", "candidate")
    @task(8)
    def get_vacancies_list(self):
        """Получение списка вакансий (кандидат или HR)"""
        token = self.candidate_token or self.hr_token
        if not token:
            return
            
        with self.client.get(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {token}"},
            catch_response=True,
            name="GET /api/v1/vacancies"
        ) as response:
            if response.status_code == 200:
                # Обновляем кэш доступных вакансий
                vacancies = response.json()
                self.available_vacancies = [v["vacancy_id"] for v in vacancies if v["vacancy_id"]]
                response.success()
            elif response.status_code == 401:
                response.failure("Unauthorized")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("get", "light")
    @task(6)
    def get_my_profile(self):
        """Получение профиля текущего пользователя"""
        token = self.candidate_token or self.hr_token
        if not token:
            return
            
        with self.client.get(
            "/api/v1/me",
            headers={"Authorization": f"Bearer {token}"},
            catch_response=True,
            name="GET /api/v1/me"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("get", "medium", "candidate")
    @task(4)
    def get_vacancy_detail(self):
        """Получение деталей конкретной вакансии"""
        if not self._ensure_has_vacancies():
            return
            
        token = self.candidate_token or self.hr_token
        vacancy_id = random.choice(self.available_vacancies)
        
        with self.client.get(
            f"/api/v1/vacancies/{vacancy_id}",
            headers={"Authorization": f"Bearer {token}"},
            catch_response=True,
            name="GET /api/v1/vacancies/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # Удаляем несуществующую вакансию из кэша
                if vacancy_id in self.available_vacancies:
                    self.available_vacancies.remove(vacancy_id)
                response.failure("Vacancy not found")
            else:
                response.failure(f"Status: {response.status_code}")

    # ========== HR-ОПЕРАЦИИ ==========
    
    @tag("hr", "create", "heavy")
    @task(3)
    def create_vacancy(self):
        """Создание новой вакансии (только HR)"""
        if not self.hr_token:
            return
            
        vacancy_data = {
            "position_title": f"{random.choice(VACANCY_TITLES)} {random.randint(1000, 9999)}",
            "job_description": random.choice(VACANCY_DESCRIPTIONS),
            "requirements": f"Требования для вакансии {random.randint(1, 100)}",
            "questions": [
                f"Вопрос по теме {random.randint(1, 10)}?",
                "Расскажите о вашем опыте?",
                "Какие технологии предпочитаете?"
            ]
        }
        
        with self.client.post(
            "/api/v1/vacancies",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            json=vacancy_data,
            catch_response=True,
            name="POST /api/v1/vacancies"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.my_vacancies.append(data["vacancy_id"])
                # Также добавляем в доступные вакансии
                if data["vacancy_id"] not in self.available_vacancies:
                    self.available_vacancies.append(data["vacancy_id"])
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("hr", "update", "medium")
    @task(2)
    def update_my_vacancy(self):
        """Обновление вакансии (только свои вакансии)"""
        if not self.hr_token or not self.my_vacancies:
            # Если нет своих вакансий, создаем одну
            if self.hr_token and not self.my_vacancies:
                self._create_initial_vacancy()
            return
            
        vacancy_id = random.choice(self.my_vacancies)
        update_data = {
            "job_description": f"Обновленное описание вакансии {datetime.now().strftime('%H:%M:%S')}",
            "requirements": "Обновленные требования"
        }
        
        with self.client.put(
            f"/api/v1/vacancies/{vacancy_id}",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            json=update_data,
            catch_response=True,
            name="PUT /api/v1/vacancies/{id}"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code in [403, 404]:
                # Удаляем вакансию из списка, если нет доступа или не найдена
                if vacancy_id in self.my_vacancies:
                    self.my_vacancies.remove(vacancy_id)
                response.failure(f"Status: {response.status_code}")
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("hr", "get", "medium")
    @task(2)
    def get_all_users(self):
        """Получение списка пользователей (только HR)"""
        if not self.hr_token:
            return
            
        with self.client.get(
            "/api/v1/users",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            catch_response=True,
            name="GET /api/v1/users"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("hr", "get", "light")
    @task(3)
    def get_statistics(self):
        """Получение статистики (только HR)"""
        if not self.hr_token:
            return
            
        with self.client.get(
            "/api/v1/statistics/overview",
            headers={"Authorization": f"Bearer {self.hr_token}"},
            catch_response=True,
            name="GET /api/v1/statistics/overview"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    # ========== КАНДИДАТ-ОПЕРАЦИИ ==========
    
    @tag("candidate", "resume", "medium")
    @task(2)
    def create_or_update_resume(self):
        """Создание или обновление резюме (только кандидат)"""
        if not self.candidate_token:
            return
            
        resume_data = {
            "birth_date": "1990-01-15",
            "contact_phone": f"+7-9{random.randint(10, 99)}-{random.randint(100, 999)}-{random.randint(10, 99)}-{random.randint(10, 99)}",
            "contact_email": f"candidate_{random.randint(1000, 9999)}@test.com",
            "education": "Высшее техническое образование",
            "work_experience": f"Опыт работы {random.randint(1, 10)} лет",
            "skills": "Python, FastAPI, PostgreSQL, Docker, Linux"
        }
        
        # Сначала пытаемся создать резюме
        with self.client.post(
            "/api/v1/resumes",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            json=resume_data,
            catch_response=True,
            name="POST /api/v1/resumes"
        ) as response:
            if response.status_code == 201:
                response.success()
            elif response.status_code == 400:
                # Если резюме уже существует, обновляем его
                self._update_existing_resume(resume_data)
            else:
                response.failure(f"Status: {response.status_code}")
    
    def _update_existing_resume(self, resume_data):
        """Обновление существующего резюме"""
        with self.client.put(
            "/api/v1/resumes/my",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            json=resume_data,
            catch_response=True,
            name="PUT /api/v1/resumes/my"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Update resume status: {response.status_code}")
    
    @tag("candidate", "get", "light")
    @task(3)
    def get_my_resume(self):
        """Получение своего резюме (только кандидат)"""
        if not self.candidate_token:
            return
            
        with self.client.get(
            "/api/v1/resumes/my",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            catch_response=True,
            name="GET /api/v1/resumes/my"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                response.success()  # Резюме еще нет - это нормально
            else:
                response.failure(f"Status: {response.status_code}")
    
    @tag("candidate", "get", "light")
    @task(2)
    def get_my_interviews(self):
        """Получение своих собеседований (только кандидат)"""
        if not self.candidate_token:
            return
            
        with self.client.get(
            "/api/v1/interviews/my",
            headers={"Authorization": f"Bearer {self.candidate_token}"},
            catch_response=True,
            name="GET /api/v1/interviews/my"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status: {response.status_code}")

    # ========== КОМПЛЕКСНЫЕ СЦЕНАРИИ ==========
    
    @tag("complex", "candidate_flow")
    @task(1)
    def candidate_comprehensive_flow(self):
        """Комплексный сценарий поведения кандидата"""
        if not self.candidate_token:
            return
        
        # 1. Просмотр списка вакансий
        self.get_vacancies_list()
        
        # 2. Просмотр профиля
        self.get_my_profile()
        
        # 3. Просмотр деталей случайной вакансии
        if self.available_vacancies:
            vacancy_id = random.choice(self.available_vacancies)
            with self.client.get(
                f"/api/v1/vacancies/{vacancy_id}",
                headers={"Authorization": f"Bearer {self.candidate_token}"},
                name="Complex: GET vacancy detail"
            ) as response:
                if response.status_code == 200:
                    pass  # Успех
        
        # 4. Работа с резюме
        self.get_my_resume()
        
        # 5. Просмотр собеседований
        self.get_my_interviews()
    
    @tag("complex", "hr_flow")
    @task(1)
    def hr_comprehensive_flow(self):
        """Комплексный сценарий поведения HR"""
        if not self.hr_token:
            return
        
        # 1. Создание вакансии
        self.create_vacancy()
        
        # 2. Просмотр пользователей
        self.get_all_users()
        
        # 3. Просмотр статистики
        self.get_statistics()
        
        # 4. Обновление своей вакансии (если есть)
        if self.my_vacancies:
            self.update_my_vacancy()
        
        # 5. Просмотр всех вакансий
        self.get_vacancies_list()


# ========== СПЕЦИАЛИЗИРОВАННЫЕ КЛАССЫ ==========

class CandidateUser(SimpleHRUser):
    """Специализированный класс для кандидатов (только чтение)"""
    wait_time = between(2.0, 5.0)
    
    def on_start(self):
        """Только регистрация кандидата"""
        test_users = get_test_users()
        self._register_user(test_users["candidate"], "candidate")
        if self.candidate_token:
            self._refresh_available_vacancies()
    
    @task(10)
    def candidate_tasks(self):
        """Задачи кандидата"""
        tasks = [
            self.get_vacancies_list,
            self.get_my_profile,
            self.get_vacancy_detail,
            self.get_my_resume,
            self.get_my_interviews
        ]
        random.choice(tasks)()


class HRUser(SimpleHRUser):
    """Специализированный класс для HR"""
    wait_time = between(1.0, 2.0)
    
    def on_start(self):
        """Только регистрация HR и создание вакансий"""
        test_users = get_test_users()
        if self._register_user(test_users["hr"], "hr"):
            # Создаем несколько начальных вакансий
            for _ in range(2):
                self._create_initial_vacancy()
            self._refresh_available_vacancies()
    
    @task(8)
    def hr_tasks(self):
        """Задачи HR"""
        tasks = [
            self.get_vacancies_list,
            self.create_vacancy,
            self.update_my_vacancy,
            self.get_all_users,
            self.get_statistics
        ]
        random.choice(tasks)()


class MixedUser(SimpleHRUser):
    """Пользователь с комбинированным поведением (HR + кандидат)"""
    wait_time = between(1.5, 3.0)
    
    @task(5)
    def light_tasks(self):
        """Легкие задачи"""
        tasks = [self.get_vacancies_list, self.get_my_profile]
        random.choice(tasks)()
    
    @task(3)
    def hr_specific_tasks(self):
        """HR задачи (если есть токен)"""
        if self.hr_token:
            tasks = [self.create_vacancy, self.get_statistics]
            random.choice(tasks)()
    
    @task(2)
    def candidate_specific_tasks(self):
        """Кандидат задачи (если есть токен)"""
        if self.candidate_token:
            tasks = [self.get_my_resume, self.get_my_interviews]
            random.choice(tasks)()
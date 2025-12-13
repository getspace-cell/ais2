"""
Утилиты для параллельной работы с DeepSeek API
Поддержка множественных API ключей и батч-обработки
"""
import json
import logging
import asyncio
import random
from typing import List, Dict, Optional, Tuple
import httpx
import os
from dotenv import load_dotenv
from itertools import cycle

load_dotenv()
logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")

# Загружаем API ключи
API_KEYS = [
    os.getenv("DEEPSEEK_API_KEY"),
    os.getenv("DEEPSEEK_API_KEY_2"),
    os.getenv("DEEPSEEK_API_KEY_3"),
    os.getenv("DEEPSEEK_API_KEY_4"),
    os.getenv("DEEPSEEK_API_KEY_5"),
]
API_KEYS = [key for key in API_KEYS if key and key.strip()]

# Загружаем прокси
PROXIES = []
proxy_str = os.getenv("PROXIES", "")
if proxy_str:
    for line in proxy_str.strip().split('\n'):
        parts = line.split('*')
        if len(parts) >= 3:
            ip_port = parts[0].strip()
            username = parts[1].strip()
            password = parts[2].strip()
            PROXIES.append(f"http://{username}:{password}@{ip_port}")

if not API_KEYS:
    raise ValueError("Не найдено ни одного валидного API ключа!")

logger.info(f"Загружено {len(API_KEYS)} API ключей")
logger.info(f"Загружено {len(PROXIES)} прокси")

api_key_pool = cycle(API_KEYS)
proxy_pool = cycle(PROXIES) if PROXIES else None


def get_next_api_key() -> str:
    """Получить следующий API ключ из пула"""
    return next(api_key_pool)


def get_next_proxy() -> Optional[str]:
    """Получить следующий прокси из пула"""
    return next(proxy_pool) if proxy_pool else None


async def parse_resume_batch_with_deepseek(
    pdf_texts: List[str],
    api_key: Optional[str] = None,
    retry_count: int = 3
) -> Dict[str, Dict]:
    """
    Парсинг батча резюме (до 4-5 резюме за раз).
    
    Args:
        pdf_texts: Список текстов PDF файлов (до 5 штук)
        api_key: API ключ (если None, берется из пула)
    
    Returns:
        Словарь с подробно распарсенными резюме
    """
    if api_key is None:
        api_key = get_next_api_key()
    
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Твоя задача - детально проанализировать {len(pdf_texts)} резюме и извлечь максимум информации для AI-анализа.

Верни JSON в формате:
{{
  "resume1": {{
    "full_name": "...",
    "contact_email": "...",
    "contact_phone": "...",
    "birth_date": "YYYY-MM-DD" или null,
    
    "education": "текстовое описание образования",
    "work_experience": "текстовое описание опыта",
    "skills": "общее описание навыков",
    
    "technical_skills": ["Python", "FastAPI", "PostgreSQL", ...],
    "soft_skills": ["Командная работа", "Коммуникабельность", ...],
    "languages": [{{"language": "Английский", "level": "B2"}}, ...],
    "certifications": ["AWS Certified", "IELTS 7.0", ...],
    "projects": [
      {{"name": "Название проекта", "description": "Краткое описание", "technologies": ["tech1", "tech2"]}},
      ...
    ],
    "desired_position": "Backend Developer" или null,
    "desired_salary": 150000 или null,
    "experience_years": 5,
    
    "ai_summary": "Краткая сводка кандидата в 2-3 предложениях",
    "ai_strengths": ["Сильная сторона 1", "Сильная сторона 2", ...],
    "ai_weaknesses": ["Слабая сторона 1", "Слабая сторона 2", ...]
  }},
  "resume2": {{ ... }}
}}

Если какое-то поле отсутствует, используй null или пустой массив [].

Тексты резюме:
{chr(10).join([f"=== РЕЗЮМЕ {i+1} ==={chr(10)}{text[:2000]}" for i, text in enumerate(pdf_texts)])}
"""
    
    try:
        proxy = get_next_proxy()
        proxies = {"http://": proxy, "https://": proxy} if proxy else None
        
        for attempt in range(retry_count):
            try:
                # Добавляем случайную задержку перед запросом
                await asyncio.sleep(random.uniform(1, 3))
                
                async with httpx.AsyncClient(timeout=180.0, proxies=proxies) as client:
                    response = await client.post(
                        DEEPSEEK_API_URL,
                        headers={
                            "Authorization": f"Bearer {api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": "tngtech/deepseek-r1t2-chimera:free",
                            "messages": [
                                {"role": "user", "content": prompt}
                            ]
                        }
                    )
                    response.raise_for_status()
                    result = response.json()
                    content = result["choices"][0]["message"]["content"]
                    
                    # Извлекаем JSON
                    if "```json" in content:
                        json_str = content.split("```json")[1].split("```")[0].strip()
                    else:
                        json_str = content.strip()

                    parsed_resumes = json.loads(json_str)
                    logger.info(f"Успешно обработан батч из {len(pdf_texts)} резюме")
                    return parsed_resumes
                    
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:
                    wait_time = (attempt + 1) * 10  # 10, 20, 30 секунд
                    logger.warning(f"429 ошибка, попытка {attempt + 1}/{retry_count}, ждем {wait_time}с")
                    await asyncio.sleep(wait_time)
                    if attempt == retry_count - 1:
                        raise
                else:
                    raise
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге батча резюме: {e}")
        raise


async def parse_resumes_with_deepseek_parallel(
    pdf_texts: List[str],
    batch_size: int = 4,
    max_concurrent: int = 3  # Уменьшено для OpenRouter
) -> Dict[str, Dict]:
    """
    Параллельная обработка большого количества резюме.
    
    Args:
        pdf_texts: Список всех текстов PDF файлов
        batch_size: Размер батча (рекомендуется 3-5)
        max_concurrent: Максимальное количество параллельных запросов
    
    Returns:
        Объединенный словарь всех распарсенных резюме
    """
    logger.info(f"Начинаем параллельную обработку {len(pdf_texts)} резюме")
    logger.info(f"Параметры: batch_size={batch_size}, max_concurrent={max_concurrent}")
    
    # Разбиваем резюме на батчи
    batches = []
    for i in range(0, len(pdf_texts), batch_size):
        batch = pdf_texts[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"Создано {len(batches)} батчей")
    
    # Создаем семафор для ограничения параллельных запросов
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_batch_with_semaphore(batch: List[str], batch_idx: int):
        """Обработка батча с учетом семафора"""
        async with semaphore:
            logger.info(f"Обрабатываю батч {batch_idx + 1}/{len(batches)} ({len(batch)} резюме)")
            try:
                result = await parse_resume_batch_with_deepseek(batch)
                logger.info(f"✓ Батч {batch_idx + 1}/{len(batches)} завершен")
                return result
            except Exception as e:
                logger.error(f"✗ Ошибка в батче {batch_idx + 1}: {e}")
                return {}
    
    # Запускаем все батчи параллельно
    tasks = [
        process_batch_with_semaphore(batch, idx) 
        for idx, batch in enumerate(batches)
    ]
    
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Объединяем результаты
    all_resumes = {}
    resume_counter = 1
    
    for batch_result in batch_results:
        if isinstance(batch_result, Exception):
            logger.error(f"Батч завершился с ошибкой: {batch_result}")
            continue
        
        if isinstance(batch_result, dict):
            # Переименовываем ключи для глобальной уникальности
            for key, value in batch_result.items():
                new_key = f"resume{resume_counter}"
                all_resumes[new_key] = value
                resume_counter += 1
    
    logger.info(f"Обработка завершена: {len(all_resumes)} из {len(pdf_texts)} резюме успешно обработаны")
    return all_resumes


async def match_candidate_to_vacancy_batch(
    candidates_data: List[Tuple[int, Dict]],
    vacancy_requirements: Dict
) -> List[Tuple[int, Dict]]:
    """
    Батч-оценка соответствия нескольких кандидатов одной вакансии.
    
    Args:
        candidates_data: Список кортежей (candidate_id, resume_data)
        vacancy_requirements: Требования вакансии
    
    Returns:
        Список кортежей (candidate_id, match_result)
    """
    api_key = get_next_api_key()
    
    # Формируем промпт для батча кандидатов
    candidates_str = ""
    for i, (cand_id, resume) in enumerate(candidates_data, 1):
        candidates_str += f"\n--- КАНДИДАТ {i} (ID: {cand_id}) ---\n"
        candidates_str += json.dumps(resume, ensure_ascii=False, indent=2)
    
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Оцени соответствие {len(candidates_data)} кандидатов вакансии по шкале 0-100.

ТРЕБОВАНИЯ ВАКАНСИИ:
{json.dumps(vacancy_requirements, ensure_ascii=False, indent=2)}

КАНДИДАТЫ:
{candidates_str}

Верни ТОЛЬКО JSON в формате:
{{
  "candidate_1": {{
    "overall_score": 85.5,
    "technical_match_score": 90.0,
    "experience_match_score": 80.0,
    "soft_skills_match_score": 85.0,
    "matched_skills": ["Python", "FastAPI", ...],
    "missing_skills": ["Docker", "Kubernetes", ...],
    "ai_recommendation": "Краткая рекомендация",
    "ai_pros": ["Преимущество 1", ...],
    "ai_cons": ["Недостаток 1", ...]
  }},
  "candidate_2": {{ ... }}
}}
"""
    
    try:
        proxy = get_next_proxy()
        proxies = {"http://": proxy, "https://": proxy} if proxy else None
        
        async with httpx.AsyncClient(timeout=120.0, proxies=proxies) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            batch_results = json.loads(json_str)
            
            # Сопоставляем результаты с ID кандидатов
            output = []
            for i, (cand_id, _) in enumerate(candidates_data, 1):
                key = f"candidate_{i}"
                if key in batch_results:
                    match_result = batch_results[key]
                    
                    # Валидация scores
                    for score_key in ['overall_score', 'technical_match_score', 
                                     'experience_match_score', 'soft_skills_match_score']:
                        if score_key in match_result:
                            match_result[score_key] = max(0.0, min(100.0, float(match_result[score_key])))
                    
                    output.append((cand_id, match_result))
            
            return output
            
    except Exception as e:
        logger.error(f"Ошибка при батч-сопоставлении: {e}")
        raise


async def match_candidates_to_vacancy_parallel(
    candidates_data: List[Tuple[int, Dict]],
    vacancy_requirements: Dict,
    batch_size: int = 4,
    max_concurrent: int = 10
) -> List[Tuple[int, Dict]]:
    """
    Параллельное сопоставление множества кандидатов с вакансией.
    
    Args:
        candidates_data: Список кортежей (candidate_id, resume_data)
        vacancy_requirements: Требования вакансии
        batch_size: Размер батча (рекомендуется 3-5)
        max_concurrent: Максимальное количество параллельных запросов
    
    Returns:
        Список всех результатов сопоставления
    """
    logger.info(f"Начинаем параллельное сопоставление {len(candidates_data)} кандидатов")
    
    # Разбиваем на батчи
    batches = []
    for i in range(0, len(candidates_data), batch_size):
        batch = candidates_data[i:i + batch_size]
        batches.append(batch)
    
    logger.info(f"Создано {len(batches)} батчей для сопоставления")
    
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def process_match_batch_with_semaphore(batch: List[Tuple[int, Dict]], batch_idx: int):
        async with semaphore:
            logger.info(f"Сопоставляю батч {batch_idx + 1}/{len(batches)} ({len(batch)} кандидатов)")
            try:
                result = await match_candidate_to_vacancy_batch(batch, vacancy_requirements)
                logger.info(f"✓ Батч сопоставления {batch_idx + 1}/{len(batches)} завершен")
                return result
            except Exception as e:
                logger.error(f"✗ Ошибка в батче сопоставления {batch_idx + 1}: {e}")
                return []
    
    tasks = [
        process_match_batch_with_semaphore(batch, idx)
        for idx, batch in enumerate(batches)
    ]
    
    batch_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Объединяем результаты
    all_matches = []
    for batch_result in batch_results:
        if isinstance(batch_result, Exception):
            logger.error(f"Батч сопоставления завершился с ошибкой: {batch_result}")
            continue
        
        if isinstance(batch_result, list):
            all_matches.extend(batch_result)
    
    logger.info(f"Сопоставление завершено: {len(all_matches)} результатов")
    return all_matches


# Обратно совместимые функции (для существующего кода)
async def parse_resumes_with_deepseek_extended(pdf_texts: List[str]) -> Dict[str, Dict]:
    """
    Обратно совместимая функция - автоматически использует параллельную обработку.
    """
    if len(pdf_texts) <= 4:
        # Если резюме мало, используем старый метод
        return await parse_resume_batch_with_deepseek(pdf_texts)
    else:
        # Если много - параллельную обработку
        return await parse_resumes_with_deepseek_parallel(pdf_texts)


async def analyze_vacancy_requirements(
    position_title: str,
    job_description: str,
    requirements: str
) -> Dict:
    """
    Анализ вакансии (без изменений, но с ротацией ключей).
    """
    api_key = get_next_api_key()
    
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Проанализируй вакансию и извлеки структурированные требования для AI-анализа кандидатов.

Позиция: {position_title}
Описание: {job_description}
Требования: {requirements}

Верни ТОЛЬКО JSON:
{{
  "required_technical_skills": ["Python", "FastAPI", ...],
  "optional_technical_skills": ["Docker", "Kubernetes", ...],
  "required_soft_skills": ["Командная работа", "Коммуникабельность", ...],
  "required_experience_years": 3,
  "required_languages": [{{"language": "Английский", "level": "B2"}}],
  "salary_range": {{"min": 100000, "max": 200000}} или null,
  "position_category": "Backend Developer" / "Frontend Developer" / etc
}}
"""
    
    try:
        proxy = get_next_proxy()
        proxies = {"http://": proxy, "https://": proxy} if proxy else None
        
        async with httpx.AsyncClient(timeout=60.0, proxies=proxies) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            return json.loads(json_str)
            
    except Exception as e:
        logger.error(f"Ошибка при анализе вакансии: {e}")
        raise


async def analyze_interview_answers(
    questions: List[str],
    answers: str,
    position_title: str
) -> Tuple[int, int]:
    """
    Анализ ответов кандидата (без изменений, с ротацией ключей).
    """
    api_key = get_next_api_key()
    
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Твоя задача проанализировать ответы кандидата на собеседование для позиции "{position_title}".

Вопросы:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(questions)])}

Ответы кандидата:
{answers}

Оцени:
1. Soft skills (коммуникация, структурированность, аргументация) - от 0 до 100
2. Confidence score (соответствие позиции, уверенность) - от 0 до 100

Формат ответа СТРОГО: <оценка soft skills> <оценка соответствия>
Например: 85 78
"""
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
            )
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"].strip()
            scores = content.split()
            soft_skills_score = int(scores[0])
            confidence_score = int(scores[1])
            
            return soft_skills_score, confidence_score
            
    except Exception as e:
        logger.error(f"Ошибка при анализе ответов: {e}")
        raise
"""
Утилиты для работы с DeepSeek API (ОБНОВЛЕННЫЕ)
"""
import json
import logging
from typing import List, Dict, Optional, Tuple
import httpx
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")


async def parse_resumes_with_deepseek_extended(pdf_texts: List[str]) -> Dict[str, Dict]:
    """
    Расширенный парсинг резюме через DeepSeek с извлечением детальной информации.
    
    Args:
        pdf_texts: Список текстов PDF файлов
    
    Returns:
        Словарь с подробно распарсенными резюме
    """
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
{chr(10).join([f"=== РЕЗЮМЕ {i+1} ==={chr(10)}{text}" for i, text in enumerate(pdf_texts)])}
"""
    
    try:
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
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
            return parsed_resumes
            
    except Exception as e:
        logger.error(f"Ошибка при парсинге резюме через DeepSeek: {e}")
        raise


async def analyze_vacancy_requirements(
    position_title: str,
    job_description: str,
    requirements: str
) -> Dict:
    """
    Анализ вакансии и извлечение структурированных требований.
    
    Args:
        position_title: Название позиции
        job_description: Описание работы
        requirements: Требования
    
    Returns:
        Словарь с структурированными требованиями
    """
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
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
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


async def match_candidate_to_vacancy(
    candidate_resume: Dict,
    vacancy_requirements: Dict
) -> Dict:
    """
    Оценка соответствия кандидата вакансии через DeepSeek.
    
    Args:
        candidate_resume: Данные резюме кандидата
        vacancy_requirements: Требования вакансии
    
    Returns:
        Словарь с оценками и рекомендациями
    """
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Оцени соответствие кандидата вакансии по шкале 0-100.

РЕЗЮМЕ КАНДИДАТА:
{json.dumps(candidate_resume, ensure_ascii=False, indent=2)}

ТРЕБОВАНИЯ ВАКАНСИИ:
{json.dumps(vacancy_requirements, ensure_ascii=False, indent=2)}

Верни ТОЛЬКО JSON:
{{
  "overall_score": 85.5,
  "technical_match_score": 90.0,
  "experience_match_score": 80.0,
  "soft_skills_match_score": 85.0,
  
  "matched_skills": ["Python", "FastAPI", ...],
  "missing_skills": ["Docker", "Kubernetes", ...],
  
  "ai_recommendation": "Краткая рекомендация 2-3 предложения",
  "ai_pros": ["Преимущество 1", "Преимущество 2", ...],
  "ai_cons": ["Недостаток 1", "Недостаток 2", ...]
}}

Оценки должны быть числами от 0 до 100.
"""
    
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                DEEPSEEK_API_URL,
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
            )
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]

            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            match_result = json.loads(json_str)
            
            # Валидация scores
            for key in ['overall_score', 'technical_match_score', 'experience_match_score', 'soft_skills_match_score']:
                if key in match_result:
                    match_result[key] = max(0.0, min(100.0, float(match_result[key])))
            
            return match_result
            
    except Exception as e:
        logger.error(f"Ошибка при сопоставлении кандидата и вакансии: {e}")
        raise


async def analyze_interview_answers(
    questions: List[str],
    answers: str,
    position_title: str
) -> Tuple[int, int]:
    """
    Анализ ответов кандидата на собеседовании (БЕЗ ИЗМЕНЕНИЙ).
    
    Args:
        questions: Список вопросов
        answers: Текстовые ответы кандидата
        position_title: Название позиции
    
    Returns:
        (soft_skills_score, confidence_score)
    """
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
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                data=json.dumps({
                    "model": "tngtech/deepseek-r1t2-chimera:free",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                })
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
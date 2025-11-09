"""
Утилиты для работы с DeepSeek API
"""
import base64
import json
import logging
from typing import List, Dict, Optional
import httpx
import os
from dotenv import load_dotenv


from PyPDF2 import PdfReader
import asyncio

from pathlib import Path
import zipfile
from io import BytesIO
import pdfplumber

from pathlib import Path
import zipfile
from typing import List
import zipfile
import io
import secrets
import string
from datetime import datetime


load_dotenv()
logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")



async def parse_resumes_with_deepseek(pdf_texts: List[str]) -> Dict[str, Dict]:
    """
    Парсинг текста резюме через DeepSeek API
    
    Args:
        pdf_texts: Список текстов PDF файлов
    
    Returns:
        Словарь с распарсенными резюме
    """
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Твоя задача распарсить данные из {len(pdf_texts)} резюме и предоставить их в формате JSON:
{{
  "resume1": {{ "full_name": "...", "skills": "...", "work_experience": "...", "education": "...", "contact_email": "...", "contact_phone": "...", "birth_date": "YYYY-MM-DD" }},
  "resume2": {{ ... }},
  ...
}}

Если какое-то поле отсутствует, используй null. Формат даты рождения: YYYY-MM-DD.

Тексты резюме:
{chr(10).join(pdf_texts)}
"""
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
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

            # Извлекаем JSON из ответа
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            else:
                json_str = content.strip()

            parsed_resumes = json.loads(json_str)
            return parsed_resumes
    except Exception as e:
        logger.error(f"Ошибка при парсинге резюме через DeepSeek: {e}")
        raise


async def analyze_interview_answers(
    questions: List[str],
    answers: str,
    position_title: str
) -> tuple[int, int]:
    """
    Анализ ответов кандидата на собеседовании через DeepSeek
    
    Args:
        questions: Список вопросов
        answers: Текстовые ответы кандидата
        position_title: Название позиции
    
    Returns:
        (soft_skills_score, confidence_score) - оценки по 100-бальной шкале
    """
    prompt = f"""НИКАКИХ дополнительных сообщений не требуется.
Твоя задача проанализировать ответы кандидата на собеседование для позиции "{position_title}" и поставить ему оценку по 100-бальной шкале.

Вопросы:
{chr(10).join([f"{i+1}. {q}" for i, q in enumerate(questions)])}

Ответы кандидата:
{answers}

Оцени:
1. Soft skills (коммуникация, структурированность мышления, аргументация) - от 0 до 100
2. Confidence score (соответствие позиции, уверенность в ответах) - от 0 до 100

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
                        {
                        "role": "user",
                        "content": prompt
                        }
                    ]
                })
            )
            response.raise_for_status()
            result = response.json()
            
            content = result["choices"][0]["message"]["content"].strip()
            
            # Парсим оценки
            scores = content.split()
            soft_skills_score = int(scores[0])
            confidence_score = int(scores[1])
            
            return soft_skills_score, confidence_score
            
    except Exception as e:
        logger.error(f"Ошибка при анализе ответов через DeepSeek: {e}")
        raise




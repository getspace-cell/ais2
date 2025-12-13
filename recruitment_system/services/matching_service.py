"""
Детерминированный алгоритм сопоставления кандидата и вакансии
БЕЗ использования AI - только на основе структурированных данных
"""
from typing import Dict, List, Optional, Tuple
from datetime import date, datetime
from models.dao import Vacancy, Resume


def calculate_experience_score(
    candidate_experience: int,
    min_required: int,
    max_required: Optional[int]
) -> int:
    """
    Оценка опыта работы (0-100)
    
    Логика:
    - Если опыт < минимума: пропорциональная оценка (50% за каждый год до минимума)
    - Если опыт в диапазоне: 100
    - Если опыт > максимума и максимум задан: небольшой штраф
    """
    if candidate_experience < min_required:
        # Недостаточно опыта - пропорциональный штраф
        if min_required == 0:
            return 100
        ratio = candidate_experience / min_required
        return int(ratio * 100)
    
    if max_required is None:
        # Нет верхней границы - любой опыт >= минимума идеален
        return 100
    
    if candidate_experience <= max_required:
        # В идеальном диапазоне
        return 100
    
    # Опыт превышает максимум - небольшой штраф (overqualified)
    excess = candidate_experience - max_required
    penalty = min(excess * 5, 20)  # Максимум -20 баллов
    return max(80, 100 - penalty)


def calculate_age_score(
    birth_date: Optional[date],
    min_age: Optional[int],
    max_age: Optional[int]
) -> int:
    """
    Оценка возраста (0-100)
    
    Логика:
    - Если возраст не указан в резюме и не требуется: 100
    - Если возраст не указан, но требуется: 0
    - Если в диапазоне: 100
    - Если вне диапазона: 0
    """
    if min_age is None and max_age is None:
        # Возраст не имеет значения
        return 100
    
    if birth_date is None:
        # Возраст не указан в резюме, но требуется
        return 0
    
    today = date.today()
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    
    if min_age is not None and age < min_age:
        return 0
    
    if max_age is not None and age > max_age:
        return 0
    
    return 100


def calculate_education_score(
    candidate_education: Optional[str],
    education_required: bool,
    education_level: Optional[str]
) -> int:
    """
    Оценка образования (0-100)
    
    Логика:
    - Если не требуется: 100
    - Если требуется, но не указано: 0
    - Проверка наличия ключевых слов в описании образования
    """
    if not education_required:
        return 100
    
    if not candidate_education:
        return 0
    
    # Проверяем наличие образования по ключевым словам
    education_lower = candidate_education.lower()
    
    if education_level:
        level_keywords = {
            'Бакалавр': ['бакалавр', 'bachelor'],
            'Магистр': ['магистр', 'master'],
            'Специалист': ['специалист', 'specialist']
        }
        
        keywords = level_keywords.get(education_level, [])
        if any(keyword in education_lower for keyword in keywords):
            return 100
        
        # Есть высшее образование, но другого уровня
        if any(word in education_lower for word in ['университет', 'институт', 'university', 'высшее']):
            return 70
        
        return 30
    
    # Просто требуется высшее образование
    if any(word in education_lower for word in ['университет', 'институт', 'university', 'высшее']):
        return 100
    
    return 30


def calculate_technical_skills_score(
    candidate_skills: List[str],
    required_skills: List[str],
    optional_skills: List[str]
) -> Tuple[int, List[str], List[str]]:
    """
    Оценка технических навыков (0-100)
    
    Логика:
    - Обязательные навыки: каждый дает 100/N баллов (где N - количество обязательных)
    - Желательные навыки: каждый дает бонус до 20 баллов
    
    Returns:
        (score, matched_skills, missing_skills)
    """
    # Нормализуем для сравнения
    candidate_skills_lower = [s.lower().strip() for s in candidate_skills]
    required_lower = [s.lower().strip() for s in required_skills]
    optional_lower = [s.lower().strip() for s in optional_skills]
    
    # Проверяем обязательные навыки
    matched_required = []
    missing_required = []
    
    for skill in required_skills:
        if skill.lower().strip() in candidate_skills_lower:
            matched_required.append(skill)
        else:
            missing_required.append(skill)
    
    # Базовый скор из обязательных навыков
    if len(required_skills) == 0:
        base_score = 100
    else:
        base_score = int((len(matched_required) / len(required_skills)) * 100)
    
    # Бонус из желательных навыков (максимум +20 баллов)
    matched_optional = [
        skill for skill in optional_skills 
        if skill.lower().strip() in candidate_skills_lower
    ]
    
    if len(optional_skills) > 0:
        bonus = int((len(matched_optional) / len(optional_skills)) * 20)
        final_score = min(100, base_score + bonus)
    else:
        final_score = base_score
    
    matched_all = matched_required + matched_optional
    
    return final_score, matched_all, missing_required


def calculate_soft_skills_score(
    candidate_soft_skills: List[str],
    required_soft_skills: List[str]
) -> Tuple[int, List[str]]:
    """
    Оценка soft skills (0-100)
    
    Логика: Процент совпадения с требуемыми навыками
    
    Returns:
        (score, matched_skills)
    """
    if len(required_soft_skills) == 0:
        return 100, []
    
    candidate_lower = [s.lower().strip() for s in candidate_soft_skills]
    
    matched = []
    for skill in required_soft_skills:
        if skill.lower().strip() in candidate_lower:
            matched.append(skill)
    
    score = int((len(matched) / len(required_soft_skills)) * 100)
    
    return score, matched


def compare_language_level(candidate_level: str, required_level: str) -> bool:
    """
    Сравнение уровней языка
    
    Уровни по возрастанию: A1 < A2 < B1 < B2 < C1 < C2
    """
    levels = ['A1', 'A2', 'B1', 'B2', 'C1', 'C2']
    
    try:
        candidate_idx = levels.index(candidate_level.upper())
        required_idx = levels.index(required_level.upper())
        return candidate_idx >= required_idx
    except ValueError:
        return False


def calculate_language_score(
    candidate_languages: List[Dict],  # [{"language": "Английский", "level": "B2"}]
    required_languages: List[Dict]    # [{"language": "Английский", "min_level": "B1"}]
) -> Tuple[int, List[str]]:
    """
    Оценка знания языков (0-100)
    
    Логика: Процент совпадения требуемых языков с достаточным уровнем
    
    Returns:
        (score, matched_languages)
    """
    if len(required_languages) == 0:
        return 100, []
    
    matched = []
    
    for req_lang in required_languages:
        req_name = req_lang['language'].lower().strip()
        req_level = req_lang['min_level']
        
        # Ищем язык у кандидата
        for cand_lang in candidate_languages:
            cand_name = cand_lang['language'].lower().strip()
            cand_level = cand_lang.get('level', 'A1')
            
            if req_name in cand_name or cand_name in req_name:
                if compare_language_level(cand_level, req_level):
                    matched.append(f"{req_lang['language']} ({cand_level})")
                    break
    
    score = int((len(matched) / len(required_languages)) * 100)
    
    return score, matched


def match_candidate_to_vacancy_deterministic(
    resume: Resume,
    vacancy: Vacancy
) -> Dict:
    """
    ГЛАВНАЯ ФУНКЦИЯ: Детерминированное сопоставление кандидата и вакансии
    
    Args:
        resume: Резюме кандидата
        vacancy: Вакансия с критериями
    
    Returns:
        Словарь с оценками и деталями
    """
    # 1. Оценка опыта
    experience_score = calculate_experience_score(
        resume.experience_years or 0,
        vacancy.min_experience_years,
        vacancy.max_experience_years
    )
    
    # 2. Оценка возраста
    age_score = calculate_age_score(
        resume.birth_date,
        vacancy.min_age,
        vacancy.max_age
    )
    
    # 3. Оценка образования
    education_score = calculate_education_score(
        resume.education,
        vacancy.education_required,
        vacancy.education_level
    )
    
    # 4. Оценка технических навыков
    technical_score, matched_tech, missing_tech = calculate_technical_skills_score(
        resume.technical_skills or [],
        vacancy.required_technical_skills or [],
        vacancy.optional_technical_skills or []
    )
    
    # 5. Оценка soft skills
    soft_score, matched_soft = calculate_soft_skills_score(
        resume.soft_skills or [],
        vacancy.required_soft_skills or []
    )
    
    # 6. Оценка языков
    language_score, matched_lang = calculate_language_score(
        resume.languages or [],
        vacancy.required_languages or []
    )
    
    # 7. Расчет общей оценки по весам
    overall_score = int(
        (experience_score * vacancy.weight_experience / 100) +
        (technical_score * vacancy.weight_technical_skills / 100) +
        (soft_score * vacancy.weight_soft_skills / 100) +
        (language_score * vacancy.weight_languages / 100)
    )
    
    # Штраф, если критичные критерии не выполнены (возраст, образование)
    if age_score == 0:
        overall_score = int(overall_score * 0.5)  # -50% если не подходит возраст
    
    if education_score < 50 and vacancy.education_required:
        overall_score = int(overall_score * 0.7)  # -30% если нет нужного образования
    
    return {
        'overall_score': max(0, min(100, overall_score)),
        'experience_score': experience_score,
        'technical_skills_score': technical_score,
        'soft_skills_score': soft_score,
        'language_score': language_score,
        'education_score': education_score,
        'age_score': age_score,
        
        'matched_technical_skills': matched_tech,
        'missing_technical_skills': missing_tech,
        'matched_soft_skills': matched_soft,
        'matched_languages': matched_lang,
        
        # AI-анализ берем из резюме (уже был сделан при парсинге)
        'ai_summary': resume.ai_summary,
        'ai_strengths': resume.ai_strengths or [],
        'ai_weaknesses': resume.ai_weaknesses or []
    }


# ========== ПРИМЕР ИСПОЛЬЗОВАНИЯ ==========

if __name__ == "__main__":
    # Пример резюме кандидата
    class MockResume:
        experience_years = 5
        birth_date = date(1995, 5, 15)  # ~29 лет
        education = "МГУ, Факультет ВМК, Бакалавр, 2017"
        technical_skills = ["Python", "FastAPI", "PostgreSQL", "Docker", "Git"]
        soft_skills = ["Командная работа", "Коммуникабельность"]
        languages = [{"language": "Английский", "level": "B2"}]
        ai_summary = "Опытный Python разработчик с 5 годами опыта"
        ai_strengths = ["Сильные технические навыки", "Опыт с микросервисами"]
        ai_weaknesses = ["Нет опыта с Kubernetes"]
    
    # Пример вакансии
    class MockVacancy:
        min_experience_years = 3
        max_experience_years = 10
        min_age = 25
        max_age = 45
        education_required = True
        education_level = "Бакалавр"
        required_technical_skills = ["Python", "FastAPI", "PostgreSQL"]
        optional_technical_skills = ["Docker", "Kubernetes", "Redis"]
        required_soft_skills = ["Командная работа"]
        required_languages = [{"language": "Английский", "min_level": "B1"}]
        weight_experience = 30
        weight_technical_skills = 40
        weight_soft_skills = 20
        weight_languages = 10
    
    result = match_candidate_to_vacancy_deterministic(MockResume(), MockVacancy())
    
    print("=== РЕЗУЛЬТАТ СОПОСТАВЛЕНИЯ ===")
    print(f"Общая оценка: {result['overall_score']}/100")
    print(f"\nДетальные оценки:")
    print(f"  Опыт: {result['experience_score']}/100")
    print(f"  Технические навыки: {result['technical_skills_score']}/100")
    print(f"  Soft skills: {result['soft_skills_score']}/100")
    print(f"  Языки: {result['language_score']}/100")
    print(f"  Образование: {result['education_score']}/100")
    print(f"  Возраст: {result['age_score']}/100")
    print(f"\nСовпали навыки: {result['matched_technical_skills']}")
    print(f"Отсутствуют навыки: {result['missing_technical_skills']}")
"""
Утилиты для отправки email уведомлений
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Настройки SMTP (загружать из .env)
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_USERNAME = os.getenv("SMTP_USERNAME")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
FROM_EMAIL = os.getenv("FROM_EMAIL")


def send_interview_invitation(
    to_email: str,
    full_name: str,
    position_title: str,
    vacancy_link: str,
    login: str,
    password: str
) -> bool:
    """
    Отправка приглашения на собеседование
    
    Args:
        to_email: Email кандидата
        full_name: Полное имя кандидата
        position_title: Название позиции
        vacancy_link: Ссылка на вакансию
        login: Логин для входа
        password: Пароль для входа
    
    Returns:
        True если отправка успешна
    """
    # Проверяем настройки SMTP
    if not SMTP_USERNAME or not SMTP_PASSWORD:
        logger.warning(f"SMTP не настроен. Email для {to_email} не отправлен (режим разработки)")
        # В режиме разработки возвращаем True и логируем приглашение
        logger.info(f"""
=== ПРИГЛАШЕНИЕ НА СОБЕСЕДОВАНИЕ (DEV MODE) ===
Кому: {to_email}
Имя: {full_name}
Позиция: {position_title}
Ссылка: {vacancy_link}
Login: {login}
Password: {password}
===============================================
        """)
        return True
    
    subject = f"Приглашение на собеседование - {position_title}"
    
    body = f"""Здравствуйте, {full_name}.

Рады пригласить вас на первый этап собеседования на позицию {position_title}.

Для прохождения интервью:
1. Перейдите по ссылке: {vacancy_link}
2. Войдите в систему, используя следующие данные:
    • Login: {login}
    • Password: {password}

3. Ответьте на предложенные вопросы голосом или текстом
4. Дождитесь результатов оценки

Если у вас возникнут вопросы, свяжитесь с нами.

С уважением,
HR отдел
"""
    
    try:
        # Создаем сообщение
        message = MIMEMultipart()
        message["From"] = FROM_EMAIL
        message["To"] = to_email
        message["Subject"] = subject
        
        message.attach(MIMEText(body, "plain", "utf-8"))
        
        # Отправляем через SMTP с таймаутом
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=10) as server:
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            server.send_message(message)
        
        logger.info(f"Приглашение отправлено на {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке email на {to_email}: {e}")
        return False


def send_bulk_invitations(invitations: List[dict]) -> dict:
    """
    Массовая отправка приглашений
    
    Args:
        invitations: Список словарей с данными для отправки
    
    Returns:
        Статистика отправки
    """
    success_count = 0
    failed_emails = []
    
    for inv in invitations:
        success = send_interview_invitation(
            to_email=inv['email'],
            full_name=inv['full_name'],
            position_title=inv['position_title'],
            vacancy_link=inv['vacancy_link'],
            login=inv['login'],
            password=inv['password']
        )
        
        if success:
            success_count += 1
        else:
            failed_emails.append(inv['email'])
    
    return {
        "total": len(invitations),
        "success": success_count,
        "failed": len(failed_emails),
        "failed_emails": failed_emails
    }




"""
Конфигурация приложения Simple HR
"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Настройки приложения"""
    
    # JWT настройки
    SECRET_KEY: str = "your-secret-key"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 часа
    
    # База данных
    DATABASE_URL: str = "sqlite:///recruitment.db"
    
    # Приложение
    APP_NAME: str = "Simple HR - Recruitment System"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    BASE_URL: str = "http://localhost:8000"
    
    # DeepSeek API
    DEEPSEEK_API_KEY: str = ""
    DEEPSEEK_API_URL: str = "https://api.deepseek.com/v1/chat/completions"
    DEEPSEEK_API_KEY_2: str = ""
    DEEPSEEK_API_KEY_3: str = ""
    DEEPSEEK_API_KEY_4: str = ""

    
    # OpenAI Whisper (Speech-to-Text)
    OPENAI_API_KEY: str = ""
    WHISPER_API_URL: str = "https://api.openai.com/v1/audio/transcriptions"
    
    # Email настройки
    SMTP_SERVER: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    FROM_EMAIL: str = "hr@company.com"
    
    # Медиа файлы
    MEDIA_DIR: str = "media/interviews"
    MAX_VIDEO_SIZE_MB: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()


# Валидация критичных настроек при запуске
def validate_settings():
    """Проверка наличия обязательных настроек"""
    errors = []
    
    if not settings.DEEPSEEK_API_KEY:
        errors.append("DEEPSEEK_API_KEY не установлен")
    
    if not settings.OPENAI_API_KEY:
        errors.append("OPENAI_API_KEY не установлен")
    
    if not settings.SMTP_USERNAME or not settings.SMTP_PASSWORD:
        errors.append("SMTP настройки не установлены")
    
    if errors:
        print("⚠️  ВНИМАНИЕ: Не все настройки заполнены:")
        for error in errors:
            print(f"   - {error}")
        print("   Некоторые функции могут работать некорректно.\n")
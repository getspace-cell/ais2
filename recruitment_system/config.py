"""
Конфигурация приложения Simple HR
"""
from pydantic_settings import BaseSettings


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
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
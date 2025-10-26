# Инициализация подключения к БД

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional

# Импортируем Base из локального модуля models
from models.dao import Base


class DatabaseRepository:
    """
    Репозиторий для работы с базой данных.
    Управляет подключением и сессиями.
    """
    
    def __init__(self, database_url: str):
        """
        Инициализация подключения к БД.
        
        Args:
            database_url: URL подключения к БД
        """
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def create_tables(self) -> None:
        """Создание всех таблиц в БД"""
        Base.metadata.create_all(self.engine)
    
    def drop_tables(self) -> None:
        """Удаление всех таблиц из БД"""
        Base.metadata.drop_all(self.engine)
    
    def get_session(self) -> Session:
        """Получение новой сессии для работы с БД"""
        return self.SessionLocal()
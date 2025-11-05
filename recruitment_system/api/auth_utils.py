"""
Утилиты для авторизации и работы с JWT токенами
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from config import settings
from models.dao import User, UserRole
from repository import DatabaseRepository

import logging
# Создаём логгер (один раз на весь модуль)
logger = logging.getLogger("auth_debug")
logger.setLevel(logging.INFO)

# Добавляем вывод в консоль
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
console.setFormatter(formatter)
logger.addHandler(console)


# Контекст для хеширования паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Security scheme для Swagger
security = HTTPBearer()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Проверка пароля"""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Хеширование пароля"""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()

    # Если есть user_id, положим в sub
    if "sub" in to_encode:
        to_encode["sub"] = str(to_encode["sub"])  # <-- важно: строка, а не int

    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Декодирование JWT токена
    
    Args:
        token: JWT токен
    
    Returns:
        Данные из токена
    
    Raises:
        HTTPException: Если токен невалиден
    """
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        logging.info(f'{token}')

        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидный токен",
            headers={"WWW-Authenticate": "Bearer"},
        )


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db_repo = None
) -> User:
    """
    Получение текущего пользователя из JWT токена
    
    Args:
        credentials: HTTP авторизационные данные
        db_repo: Репозиторий БД
    
    Returns:
        Объект пользователя
    
    Raises:
        HTTPException: Если пользователь не найден или токен невалиден
    """
    token = credentials.credentials
    payload = decode_token(token)
    
    user_id: int = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Невалидные авторизационные данные",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Если db_repo не передан, создаем новый
    if db_repo is None:
        db_repo = DatabaseRepository(settings.DATABASE_URL)
    
    session = db_repo.get_session()
    try:
        user = session.query(User).filter(User.user_id == user_id).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Пользователь не найден",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return user
    finally:
        session.close()


def get_current_hr(current_user: User = Depends(get_current_user)) -> User:
    """
    Проверка что текущий пользователь - HR
    
    Args:
        current_user: Текущий пользователь
    
    Returns:
        Объект пользователя-HR
    
    Raises:
        HTTPException: Если пользователь не HR
    """
    if current_user.role != UserRole.HR:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только для HR"
        )
    return current_user


def get_current_candidate(current_user: User = Depends(get_current_user)) -> User:
    """
    Проверка что текущий пользователь - кандидат
    
    Args:
        current_user: Текущий пользователь
    
    Returns:
        Объект пользователя-кандидата
    
    Raises:
        HTTPException: Если пользователь не кандидат
    """
    if current_user.role != UserRole.CANDIDATE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только для кандидатов"
        )
    return current_user
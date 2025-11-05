from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.openapi.utils import get_openapi
from api.routes import router
from config import settings

app = FastAPI(
    title="Simple HR - Recruitment System API",
    description="""
    🎯 **RESTful API для системы автоматизированного рекрутинга Simple HR**
    
    ## 🔐 Авторизация
    
    Система использует JWT токены для авторизации:
    
    1. **Регистрация**: `POST /api/v1/register` - создайте аккаунт (HR или Кандидат)
    2. **Вход**: `POST /api/v1/login` - получите JWT токен
    3. **Использование**: Нажмите кнопку 🔓 **Authorize** справа вверху и введите токен в формате: `Bearer YOUR_TOKEN`
    
    После авторизации вы получите доступ к защищенным эндпоинтам в зависимости от вашей роли.
    
    ---
    
    ## 👥 Роли пользователей
    
    ### **HR (Рекрутер)**
    - Создание и управление вакансиями
    - Просмотр резюме всех кандидатов
    - Проведение собеседований (оба этапа)
    - Создание отчетов о кандидатах
    - Просмотр статистики системы
    
    ### **Кандидат**
    - Создание и редактирование своего резюме
    - Просмотр открытых вакансий
    - Просмотр своих собеседований
    - Просмотр отчетов о себе
    
    ---
    
    ## 📋 Основная функциональность
    
    * 🔐 **Авторизация/Регистрация** с JWT токенами
    * 👥 **Управление пользователями** (HR и кандидаты)
    * 💼 **Управление вакансиями** (CRUD операции)
    * 📄 **Управление резюме** (создание, чтение, обновление)
    * 🎤 **Система собеседований** (2 этапа: soft skills + hard skills)
    * 📊 **Отчеты и статистика** по кандидатам
    
    ---
    
    ## 🛠️ Технологии
    
    * **Backend**: Python 3.9+ + FastAPI
    * **ORM**: SQLAlchemy 2.0
    * **БД**: SQLite / MariaDB
    * **Auth**: JWT (python-jose + passlib)
    * **Docs**: OpenAPI 3.0 (Swagger UI)
    
    ---
    
    ## 📚 Документация
    
    * **Swagger UI**: `/docs` (текущая страница)
    * **ReDoc**: `/redoc` (альтернативная документация)
    * **OpenAPI Schema**: `/openapi.json`
    
    ---
    
    **Лабораторная работа №3** - Разработка RESTful веб-сервиса  
    **Автор:** Руслан  
    **Версия:** 1.0.0
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {
            "name": "Simple HR API",
            "description": "Основные операции системы рекрутинга"
        }
    ]
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер
app.include_router(router)


def custom_openapi():
    """Кастомная схема OpenAPI с настройками безопасности"""
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        description=app.description,
        routes=app.routes,
    )
    
    # Добавляем схему безопасности для JWT
    openapi_schema["components"]["securitySchemes"] = {
        "HTTPBearer": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Введите JWT токен (получите его через /login или /register)"
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.get("/", include_in_schema=False)
async def root():
    """Редирект на документацию"""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"], summary="Health Check")
async def health_check():
    """
    Проверка работоспособности API.
    
    Возвращает статус сервиса и версию.
    """
    return {
        "status": "healthy",
        "message": "Simple HR API is running",
        "version": settings.VERSION,
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    
    print("=" * 80)
    print("🚀 Запуск Simple HR API...")
    print("=" * 80)
    print(f"📚 Swagger UI:  http://127.0.0.1:8000/docs")
    print(f"📖 ReDoc:       http://127.0.0.1:8000/redoc")
    print(f"🔐 Auth:        JWT токены (регистрация/вход через /api/v1/register или /login)")
    print("=" * 80)
    print("\n💡 Быстрый старт:")
    print("   1. Откройте http://127.0.0.1:8000/docs")
    print("   2. Зарегистрируйтесь через POST /api/v1/register")
    print("   3. Скопируйте полученный access_token")
    print("   4. Нажмите 🔓 Authorize и вставьте токен")
    print("   5. Теперь вы можете использовать защищенные эндпоинты!\n")
    print("=" * 80)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
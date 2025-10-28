from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from api.routes import router

app = FastAPI(
    title="Simple HR - Recruitment System API",
    description="""
    🎯 **RESTful API для системы автоматизированного рекрутинга Simple HR**
    
    ## Функциональность:
    
    * 👥 **Управление пользователями** (HR и кандидаты)
    * 💼 **Управление вакансиями**
    * 📄 **Управление резюме**
    * 🎤 **Система собеседований** (2 этапа)
    * 📊 **Отчеты и статистика**
    
    ## Технологии:
    * Python + FastAPI
    * SQLAlchemy ORM
    * SQLite / MariaDB
    
    ---
    
    **Лабораторная работа №3**
    
    **Автор:** Руслан
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутер
app.include_router(router)


@app.get("/", include_in_schema=False)
async def root():
    """Редирект на документацию"""
    return RedirectResponse(url="/docs")


@app.get("/health", tags=["System"])
async def health_check():
    """Проверка работоспособности API"""
    return {
        "status": "healthy",
        "message": "Simple HR API is running",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn
    print("=" * 60)
    print("🚀 Запуск Simple HR API...")
    print("=" * 60)
    print("📚 Swagger UI: http://127.0.0.1:8000/docs")
    print("📖 ReDoc: http://127.0.0.1:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
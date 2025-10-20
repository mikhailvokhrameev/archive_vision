# /main.py
from fastapi import FastAPI
from api.v1.api import api_router
from db.init_db import init_db
from core.config import settings

app = FastAPI(
    title="Document Processing API",
    description="API для загрузки, обработки и верификации архивных документов.",
    version="1.0.0"
)

@app.on_event("startup")
def on_startup():
    # Создаем таблицы в БД при запуске приложения
    init_db()

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
def read_root():
    return {"message": "Welcome to Document Processing API"}

# Для запуска используйте команду: uvicorn main:app --reload

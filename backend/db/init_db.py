# /db/init_db.py
from sqlalchemy.orm import Session
from core.database import engine, Base

def init_db():
    # Создаем все таблицы, определенные в моделях
    Base.metadata.create_all(bind=engine)

from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

# --- Конфигурация ---
# В реальном приложении используйте переменную окружения или конфигурационный файл
DATABASE_URL = "sqlite:///./sql_app.db"

# Создание движка SQLAlchemy
# 'check_same_thread': False необходимо для SQLite, если к нему обращаются несколько потоков
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

# Базовый класс для декларативных моделей
Base = declarative_base()

# --- Отсутствующая Модель (Исправление) ---
class SavedData(Base):
    """
    Модель SQLAlchemy для сохраненных данных бота. Это та модель,
    которая вызывала 'ImportError' в bot_app.py.
    """
    __tablename__ = "saved_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True, comment="ID пользователя, взаимодействующего с ботом")
    data_key = Column(String, index=True, comment="Ключ для сохраняемых данных")
    value = Column(String, comment="Фактическое содержимое данных")

# --- Настройка Сессии ---
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Инициализирует базу данных, создавая все таблицы, если они не существуют."""
    print("Инициализация базы данных: Создание таблиц...")
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    """Функция-зависимость для получения сессии базы данных."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

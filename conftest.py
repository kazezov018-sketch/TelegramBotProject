import pytest
import asyncio
import os
from databases import Database
import typing

# Используйте переменную окружения для CI или локальное значение по умолчанию
# В CI убедитесь, что переменная TEST_DATABASE_URL установлена правильно
DB_URL = os.getenv("TEST_DATABASE_URL", "postgresql://user:password@localhost:5432/test_db")

# 1. Фиксация Event Loop на уровне сессии (Решает проблему "different loop")
# Это гарантирует, что все асинхронные фикстуры используют один и тот же контур.
@pytest.fixture(scope="session")
def event_loop():
    """Переопределяет event_loop для фиксации его области видимости на 'session'."""
    # Получаем новый контур
    loop = asyncio.get_event_loop_policy().new_event_loop()
    # Устанавливаем его как текущий
    asyncio.set_event_loop(loop)
    yield loop
    # Закрываем по завершении
    loop.close()


# 2. Фикстура базы данных на уровне сессии
@pytest.fixture(scope="session")
async def db_connection():
    """
    Создает объект базы данных, подключается, предоставляет его тестам
    и корректно закрывает.
    """
    if not DB_URL:
        pytest.fail("Переменная окружения TEST_DATABASE_URL не установлена.")

    database = Database(DB_URL)

    print(f"\n--- Подключение к DB: {DB_URL} ---")

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"Не удалось подключиться к PostgreSQL: {e}")

    # Создание таблицы (Убедитесь, что эта таблица создается только один раз за сессию)
    CREATE_TABLE_QUERY = """
    CREATE TABLE IF NOT EXISTS user_data (
        id SERIAL PRIMARY KEY,
        chat_id BIGINT NOT NULL,
        username VARCHAR(255),
        data_text TEXT NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    await database.execute(CREATE_TABLE_QUERY)

    yield database

    # Корректное закрытие пула после завершения всех тестов сессии
    print("--- Отключение от DB ---")
    await database.disconnect()


# 3. Фикстура для изоляции тестов (scope="function" по умолчанию)
# Очищает таблицу перед каждым тестом, гарантируя изоляцию.
@pytest.fixture()
async def cleanup_db_data(db_connection: Database):
    """
    Очищает таблицу user_data перед каждым тестом.
    Должен быть явно передан в тестовые функции.
    """
    # Setup: Очистка перед тестом
    await db_connection.execute("DELETE FROM user_data;")

    yield

    # Teardown: (Опционально)
    # Здесь можно добавить дополнительную очистку, если это необходимо.

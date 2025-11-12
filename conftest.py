import pytest
import asyncio
import os
from databases import Database
import pytest_asyncio

# CI үшін айнымалы ортаны пайдалану
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Запасное значение для локального запуска
    DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"


# 1. Event Loop-ты Сессияда бекіту
@pytest.fixture(scope="session")
def event_loop():
    """Фиксирует Event Loop в области видимости 'session'."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# 2. Асинхронды DB фикстурасы: scope="session" (КРИТИЧЕСКОЕ ИЗМЕНЕНИЕ)
# Используется scope="session" для соответствия event_loop и устранения конфликтов пула.
@pytest_asyncio.fixture(scope="session")
async def db_connection():
    """
    Устанавливает асинхронное соединение с БД и создает таблицу.
    Область видимости: session.
    """
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL не установлен.")

    database = Database(DATABASE_URL)

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"Не удалось подключиться к PostgreSQL: {e}")

    # Создание таблицы
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

    # Сессия аяқталғаннан кейінгі тазалау
    await database.execute("DROP TABLE user_data;")
    await database.disconnect()


# 3. Асинхронды Тазалау фикстурасы: Удалена избыточная очистка в Teardown
@pytest_asyncio.fixture(scope="function")
async def cleanup_db_data(db_connection: Database):
    """Очищает таблицу user_data перед каждым тестом (только Setup)."""

    # Setup: Очистка перед тестом (Обязательно!)
    await db_connection.execute("DELETE FROM user_data;")

    yield
    
    pass

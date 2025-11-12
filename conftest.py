import pytest
import asyncio
import os
from databases import Database
import pytest_asyncio

# CI үшін айнымалы ортаны пайдалану
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Жергілікті орындау үшін запас мән
    DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"


# 1. Event Loop-ты Сессияда бекіту (pytest-asyncio талабы)
@pytest.fixture(scope="session")
def event_loop():
    """Event Loop-ты сессия деңгейінде бекітеді."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


# 2. Асинхронды DB фикстурасы: @pytest_asyncio.fixture қолданылады
@pytest_asyncio.fixture(scope="module")
async def db_connection():
    """DB-ға қосылуды орнатады және кестені жасайды."""
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL орнатылмаған.")

    database = Database(DATABASE_URL)

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"PostgreSQL-ге қосылу мүмкін болмады: {e}")

    # Кестені жасау
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

    # Модуль аяқталғаннан кейінгі тазалау
    await database.execute("DROP TABLE user_data;")
    await database.disconnect()


# 3. Асинхронды Тазалау фикстурасы: @pytest_asyncio.fixture қолданылады
@pytest_asyncio.fixture(scope="function")
async def cleanup_db_data(db_connection: Database):
    """Әр тест алдында user_data кестесін тазалайды."""

    # Setup: Тест алдында тазалау
    await db_connection.execute("DELETE FROM user_data;")

    yield

    # Teardown: Тестен кейінгі тазалау
    await db_connection.execute("DELETE FROM user_data;")

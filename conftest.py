import pytest
import asyncio
from databases import Database
import os
# Если DB_URL определен через ENV, используйте его. Иначе укажите явно.
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


# 2. Фикстура базы данных на уровне сессии (Улучшает стабильность подключения)
@pytest.fixture(scope="session")
async def db_connection():
    """
    Создает объект базы данных, подключается,
    предоставляет его тестам и корректно закрывает.
    """
    database = Database(DB_URL)

    print(f"\n--- Подключение к DB: {DB_URL} ---")
    await database.connect()

    yield database

    # 3. Корректное закрытие пула (Решает проблему "InterfaceError")
    print("--- Отключение от DB ---")
    await database.disconnect()


# 3. Фикстура для изоляции тестов (Опционально, но рекомендуется)
# Гарантирует, что данные между тестами не пересекаются.
@pytest.fixture()
async def cleanup_db_data(db_connection: Database):
    """Очищает таблицу user_data перед каждым тестом."""

    await db_connection.execute("DELETE FROM user_data;")

    yield

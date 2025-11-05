import pytest
import os
import asyncio
from databases import Database
import asyncpg # Необходим для корректной работы databases с PostgreSQL
import datetime

# --- Конфигурация для CI ---
# CI-пайплайн устанавливает эту переменную: postgresql://ci_user:ci_password@localhost:5432/ci_test_db
DATABASE_URL = os.getenv("DATABASE_URL")

# --- Фикстура для Подключения к БД ---

@pytest.fixture(scope="module")
async def db_connection():
    """
    Устанавливает асинхронное соединение с тестовой БД PostgreSQL
    и гарантирует, что таблица user_data существует.
    """
    if not DATABASE_URL:
        # Это сработает только если кто-то запустил тест без CI
        pytest.fail("DATABASE_URL не установлен. Запуск только в CI или с переменной окружения.")

    database = Database(DATABASE_URL)

    try:
        # Подключение к БД
        await database.connect()
    except Exception as e:
        pytest.fail(f"Не удалось подключиться к PostgreSQL: {e}")

    # Создание таблицы (как в bot_app.py)
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

    # Предоставляем соединение для тестов
    yield database

    # Очистка после выполнения всех тестов модуля
    await database.execute("DROP TABLE user_data;")
    await database.disconnect()

# --- Тесты Асинхронных Операций ---

@pytest.mark.asyncio
async def test_db_connection_success(db_connection: Database):
    """Проверяет, что соединение с БД активно."""
    assert db_connection.is_connected == True

@pytest.mark.asyncio
async def test_data_insertion_and_fetch(db_connection: Database):
    """Тестирует вставку одной записи и ее последующее извлечение."""

    test_data = {
        "chat_id": 10001,
        "username": "tester_ci",
        "data_text": "CI data insertion test"
    }

    INSERT_QUERY = """
    INSERT INTO user_data (chat_id, username, data_text)
    VALUES (:chat_id, :username, :data_text)
    """

    # 1. Вставка (INSERT)
    await db_connection.execute(query=INSERT_QUERY, values=test_data)

    # 2. Извлечение (SELECT)
    SELECT_QUERY = "SELECT data_text, chat_id FROM user_data WHERE chat_id = :chat_id"
    record = await db_connection.fetch_one(query=SELECT_QUERY, values={"chat_id": test_data['chat_id']})

    # 3. Проверка
    assert record is not None
    assert record['data_text'] == test_data['data_text']

@pytest.mark.asyncio
async def test_fetch_limit_and_order(db_connection: Database):
    """
    Проверяет, что /fetch команда (LIMIT 5, ORDER BY DESC) работает корректно.
    Сначала очистим таблицу от предыдущих тестов, чтобы убедиться в точности
    (хотя фикстура должна делать это сама, это дополнительная гарантия).
    """

    await db_connection.execute("DELETE FROM user_data;")

    # Вставляем 6 записей с разными временными метками для проверки порядка
    for i in range(1, 7):
        data_text = f"Entry_{i}"
        # Делаем задержку, чтобы timestamps были гарантированно разные
        await db_connection.execute(
            "INSERT INTO user_data (chat_id, username, data_text) VALUES (9999, 'order_test', :text)",
            values={"text": data_text}
        )
        await asyncio.sleep(0.01)

    # Спрашиваем 5 последних записей
    SELECT_QUERY = """
    SELECT data_text FROM user_data
    ORDER BY created_at DESC
    LIMIT 5;
    """
    records = await db_connection.fetch_all(query=SELECT_QUERY)

    # Проверка: должно быть 5 записей
    assert len(records) == 5

    # Проверка порядка: последняя вставленная (Entry_6) должна быть первой в списке
    assert records[0]['data_text'] == "Entry_6"
    assert records[-1]['data_text'] == "Entry_2" # Entry_1 не попадет в LIMIT 5

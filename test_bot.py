import pytest
import pytest_asyncio # Импорт
import os
import asyncio
from databases import Database
import asyncpg
import datetime

DATABASE_URL = os.getenv("DATABASE_URL")


@pytest_asyncio.fixture(scope="module")
async def db_connection():
    """
    Устанавливает асинхронное соединение с тестовой БД PostgreSQL
    и гарантирует, что таблица user_data существует.
    """
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL не установлен.")

    database = Database(DATABASE_URL)

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"Не удалось подключиться к PostgreSQL: {e}")

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

    await database.execute("DROP TABLE user_data;")
    await database.disconnect()

@pytest.mark.asyncio
async def test_db_connection_success(db_connection: Database, event_loop): # <-- event_loop қосылды
    """Проверяет, что соединение с БД активно."""
    assert db_connection.is_connected == True

@pytest.mark.asyncio
async def test_data_insertion_and_fetch(db_connection: Database, event_loop): # <-- event_loop қосылды
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

    await db_connection.execute(query=INSERT_QUERY, values=test_data
    SELECT_QUERY = "SELECT data_text, chat_id FROM user_data WHERE chat_id = :chat_id"
    record = await db_connection.fetch_one(query=SELECT_QUERY, values={"chat_id": test_data['chat_id']})
    assert record is not None
    assert record['data_text'] == test_data['data_text']

@pytest.mark.asyncio
async def test_fetch_limit_and_order(db_connection: Database, event_loop): # <-- event_loop қосылды
    """
    Проверяет, что /fetch команда (LIMIT 5, ORDER BY DESC) работает корректно.
    """

    await db_connection.execute("DELETE FROM user_data;")
    for i in range(1, 7):
        data_text = f"Entry_{i}"
        await db_connection.execute(
            "INSERT INTO user_data (chat_id, username, data_text) VALUES (9999, 'order_test', :text)",
            values={"text": data_text}
        )
        await db_connection.fetch_one("SELECT 1;")

    SELECT_QUERY = """
    SELECT data_text FROM user_data
    ORDER BY created_at DESC
    LIMIT 5;
    """
    records = await db_connection.fetch_all(query=SELECT_QUERY)
    assert records[0]['data_text'] == "Entry_6"
    assert records[-1]['data_text'] == "Entry_2"

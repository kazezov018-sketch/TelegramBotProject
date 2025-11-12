import pytest
from databases import Database
# db_connection және cleanup_db_data фикстуралары conftest.py файлынан автоматты түрде импортталады

# --- Тестілер ---

@pytest.mark.asyncio
async def test_db_connection_success(db_connection: Database):
    """Базалық қосылымның белсенді екенін тексереді."""
    assert db_connection.is_connected == True

@pytest.mark.asyncio
async def test_data_insertion_and_fetch(db_connection: Database, cleanup_db_data):
    """
    Бір жазбаны енгізуді және оны кейіннен алуды тексереді.
    cleanup_db_data фикстурасы тест басталғанға дейін кестенің таза болуын қамтамасыз етеді.
    """

    test_data = {
        "chat_id": 10001,
        "username": "tester_ci",
        "data_text": "CI data insertion test"
    }

    INSERT_QUERY = """
    INSERT INTO user_data (chat_id, username, data_text)
    VALUES (:chat_id, :username, :data_text)
    """

    # 1. Енгізу (INSERT)
    await db_connection.execute(query=INSERT_QUERY, values=test_data)

    # 2. Алу (SELECT)
    SELECT_QUERY = "SELECT data_text, chat_id FROM user_data WHERE chat_id = :chat_id"
    record = await db_connection.fetch_one(query=SELECT_QUERY, values={"chat_id": test_data['chat_id']})

    # 3. Тексеру
    assert record is not None
    assert record['data_text'] == test_data['data_text']

@pytest.mark.asyncio
async def test_fetch_limit_and_order(db_connection: Database, cleanup_db_data):
    """
    /fetch командасының (LIMIT 5, ORDER BY created_at DESC) дұрыс жұмыс істеуін тексереді.
    cleanup_db_data фикстурасы тест басталғанға дейін кестенің таза болуын қамтамасыз етеді.
    """

    # 6 жазбаны енгізу
    for i in range(1, 7):
        data_text = f"Entry_{i}"
        await db_connection.execute(
            "INSERT INTO user_data (chat_id, username, data_text) VALUES (9999, 'order_test', :text)",
            values={"text": data_text}
        )
        # SELECT 1; әр енгізуден кейін TIMESTAMP-тың бірегейлігін қамтамасыз етуге көмектеседі
        await db_connection.fetch_one("SELECT 1;")

    # Соңғы 5 жазбаны сұрау
    SELECT_QUERY = """
    SELECT data_text FROM user_data
    ORDER BY created_at DESC
    LIMIT 5;
    """
    records = await db_connection.fetch_all(query=SELECT_QUERY)

    # Тексеру
    assert len(records) == 5
    assert records[0]['data_text'] == "Entry_6" # Ең соңғы жазба
    assert records[-1]['data_text'] == "Entry_2" # Соңынан бесінші жазба

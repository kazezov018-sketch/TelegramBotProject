import pytest
import asyncio
import os
from databases import Database
import pytest_asyncio

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default fallback for local execution
    DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"


# 1. Database Connection Fixture (Session Scope)
# Scope is set to 'session' for pool efficiency and compatibility with async loop config.
@pytest_asyncio.fixture(scope="session")
async def db_connection():
    """
    Establishes an asynchronous database connection pool and creates the table.
    """
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL environment variable is not set.")

    database = Database(DATABASE_URL)

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL: {e}")

    # Create the necessary table
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

    # Session Teardown: Drop the table and disconnect the pool
    await database.execute("DROP TABLE user_data;")
    await database.disconnect()


# 2. Cleanup Fixture (Function Scope)
@pytest_asyncio.fixture(scope="function")
async def cleanup_db_data(db_connection: Database):
    """
    Cleans the user_data table before each test.
    Teardown is empty to prevent connection reset errors (InterfaceError).
    """

    # Setup: Delete all rows before running the test
    await db_connection.execute("DELETE FROM user_data;")

    yield

    # Teardown: Empty pass
    pass

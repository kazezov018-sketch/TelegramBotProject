import pytest
import os
from databases import Database
import pytest_asyncio

# Get database URL from environment variable
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Default fallback for local execution
    DATABASE_URL = "postgresql://user:password@localhost:5432/test_db"


# Database Connection Fixture (Function Scope)
@pytest_asyncio.fixture(scope="function")
async def db_connection():
    """
    Establishes an asynchronous database connection pool, creates the table,
    and handles cleanup for each test function.
    """
    if not DATABASE_URL:
        pytest.fail("DATABASE_URL environment variable is not set.")

    database = Database(DATABASE_URL)

    try:
        await database.connect()
    except Exception as e:
        pytest.fail(f"Failed to connect to PostgreSQL: {e}")

    # --- Setup Phase (Before Test) ---

    # 1. Create the necessary table
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

    # 2. Clean up any existing data before test run
    await database.execute("DELETE FROM user_data;")

    yield database

    # --- Teardown Phase (After Test) ---
    # Drop the table and disconnect the pool
    await database.execute("DROP TABLE user_data;")
    await database.disconnect()

# NOTE: The separate cleanup_db_data fixture is no longer needed.

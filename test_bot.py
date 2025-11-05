import os
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database import Base, SavedData, get_db

# --- Тестке арналған Конфигурация ---
# Тесттерді негізгі дерекқордан бөлу үшін, ЖАҢА дерекқорды қолданамыз
TEST_DATABASE_URL = "sqlite:///./data/test_db.db"

# Тест Engine, Base және SessionLocal құру
test_engine = create_engine(
    TEST_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

# Барлық тесттерді орындау алдында кестелерді құру
Base.metadata.create_all(bind=test_engine)

# --- Тестке арналған get_db() функциясын алмастыру ---
# Бұл функция get_db-ге ұқсас, бірақ тест дерекқорымен жұмыс істейді
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

# --- Тесттер ---

@pytest.fixture
def test_db():
    """Әрбір тесттен кейін дерекқорды тазалайтын фикстура"""
    db = next(override_get_db())
    try:
        yield db
    finally:
        # Тест аяқталғаннан кейін барлық жазбаларды жою
        db.query(SavedData).delete()
        db.commit()

def test_create_and_read_data(test_db):
    """Жаңа деректер жазбасын құру және оны оқып шығуды тексереді."""

    test_text = "Тестілеу арқылы сақталған мәтін"

    # 1. Құру (Сақтау)
    new_data = SavedData(text=test_text)
    test_db.add(new_data)
    test_db.commit()
    test_db.refresh(new_data)

    # 2. Тексеру (Оқу)
    saved_data = test_db.query(SavedData).filter(SavedData.text == test_text).first()

    assert saved_data is not None
    assert saved_data.text == test_text
    assert saved_data.status == "Сәтті жіберілді және сақталды"
    assert saved_data.id == new_data.id

def test_default_status_and_timestamp(test_db):
    """Дефолтты мәндердің (status, timestamp) дұрыс орнатылғанын тексереді."""

    test_text = "Статус тесті"

    new_data = SavedData(text=test_text)
    test_db.add(new_data)
    test_db.commit()
    test_db.refresh(new_data)

    assert new_data.status == "Сәтті жіберілді және сақталды"
    # timestamp-тың datetime объектісі екенін тексереміз
    assert new_data.timestamp is not None

def test_fetch_data_order(test_db):
    """Деректердің уақыт бойынша дұрыс сұрыпталғанын тексереді."""

    # 1-ші жазбаны сақтау
    data1 = SavedData(text="Бірінші", timestamp=datetime(2025, 1, 1, 10, 0, 0))
    # 2-ші жазбаны сақтау
    data2 = SavedData(text="Екінші", timestamp=datetime(2025, 1, 1, 11, 0, 0))

    test_db.add_all([data1, data2])
    test_db.commit()

    # Ең жаңасынан (уақыттың кемуі бойынша) сұрыптап алу
    results = test_db.query(SavedData).order_by(SavedData.timestamp.desc()).all()

    # Екінші жазба (11:00) бірінші болуы керек
    assert results[0].text == "Екінші"
    # Бірінші жазба (10:00) екінші болуы керек
    assert results[1].text == "Бірінші"

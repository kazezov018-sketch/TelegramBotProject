import uvicorn
from bot_app import app

def start_application():
    """
    Запускает приложение FastAPI с помощью Uvicorn.

    Для запуска приложения bot_app.py мы используем Uvicorn.
    Параметр 'reload=True' полезен для разработки, так как он
    перезагружает сервер при изменении кода.
    """
    print("Подготовка к запуску Uvicorn...")
    uvicorn.run(
        "bot_app:app",
        host="0.0.0.0",
        port=8000,
        reload=True  # Перезагрузка при изменениях кода (только для разработки)
    )

if __name__ == "__main__":
    start_application()

# Инструкция по запуску:
# 1. Установите зависимости: pip install fastapi uvicorn sqlalchemy pydantic
# 2. Запустите этот файл: python main.py

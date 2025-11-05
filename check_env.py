import os
from dotenv import load_dotenv

# Попытка загрузить переменные из .env
load_dotenv()

# Получаем токен
token = os.getenv("TELEGRAM_BOT_TOKEN")

print("--- Диагностика окружения ---")

if token:
    # Если токен есть, печатаем только начало (для безопасности)
    print(f"✅ TELEGRAM_BOT_TOKEN успешно загружен. Длина: {len(token)}")
    print(f"✅ PUBLIC_URL успешно загружен: {os.getenv('PUBLIC_URL')}")
else:
    # Если токена нет, это проблема
    print("❌ ОШИБКА: TELEGRAM_BOT_TOKEN не загружен!")

# Проверка, что Python находит .env
try:
    with open(".env", "r") as f:
        print(f"✅ Файл .env найден в текущей папке.")
except FileNotFoundError:
    print("❌ ОШИБКА: Файл .env НЕ НАЙДЕН в текущей рабочей папке Gunicorn.")

print("-----------------------------")

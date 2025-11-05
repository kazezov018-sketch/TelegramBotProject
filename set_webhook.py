import os
import requests
import json
import sys
from dotenv import load_dotenv

# Загрузка переменных окружения из файла .env
load_dotenv()

# --- КОНФИГУРАЦИЯ ИЗ ОКРУЖЕНИЯ ---
# Используем PUBLIC_URL, который может быть ngrok, доменным именем или IP
PUBLIC_URL = os.getenv("PUBLIC_URL")
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Проверяем наличие всех необходимых переменных
if not BOT_TOKEN or not PUBLIC_URL:
    print("❌ Ошибка: Убедитесь, что TELEGRAM_BOT_TOKEN и PUBLIC_URL установлены в .env.")
    sys.exit(1)

# Полный URL, который Telegram будет вызывать (ваш хост + путь в FastAPI)
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{PUBLIC_URL}{WEBHOOK_PATH}"

# API URL для Telegram
TELEGRAM_API = f"https://api.telegram.org/bot{BOT_TOKEN}"
# ---

def get_webhook_info():
    """Проверяет текущий статус вебхука."""
    print("✨ Проверяю текущий вебхук...")
    try:
        response = requests.get(f"{TELEGRAM_API}/getWebhookInfo")
        response.raise_for_status()
        info = response.json()
        print(json.dumps(info, indent=4, ensure_ascii=False))
        return info
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при получении информации о вебхуке: {e}")
        return None

def set_new_webhook():
    """Устанавливает новый вебхук."""
    print(f"\n🚀 Устанавливаю новый вебхук на: {WEBHOOK_URL}")
    try:
        # Устанавливаем новый вебхук
        response = requests.post(f"{TELEGRAM_API}/setWebhook", data={'url': WEBHOOK_URL})
        response.raise_for_status()
        result = response.json()

        if result.get("ok"):
            print("✅ Успех! Вебхук успешно установлен.")
        else:
            print(f"❌ Ошибка установки вебхука: {result.get('description')}")
        print(json.dumps(result, indent=4, ensure_ascii=False))

    except requests.exceptions.RequestException as e:
        print(f"❌ Критическая ошибка при установке вебхука: {e}")

def main():
    """Основная функция, управляющая процессом установки вебхука."""

    info = get_webhook_info()

    if info and info.get("ok"):
        current_url = info.get("result", {}).get("url")
        if current_url == WEBHOOK_URL:
            print("\n✅ Вебхук уже установлен и актуален!")
            # Проверяем, есть ли ожидающие обновления
            pending_count = info.get("result", {}).get("pending_update_count", 0)
            if pending_count > 0:
                print(f"❗ **ВНИМАНИЕ:** Имеется {pending_count} ожидающих обновлений.")
                print("Запустите или проверьте ваш сервер (Gunicorn), чтобы обработать их.")
            return

    # Если вебхук не установлен, или URL изменился, устанавливаем новый
    set_new_webhook()

if __name__ == "__main__":
    main()

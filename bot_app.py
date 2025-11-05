import logging
import os
import asyncio
from dotenv import load_dotenv
from telegram import Update, Request # Импортируем Request для пользовательских настроек таймаута
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from fastapi import FastAPI, Request as FastAPIRequest
from starlette.responses import JSONResponse
from databases import Database # Асинхронная библиотека для работы с базами данных
import datetime
import json

# Загрузка переменных окружения
load_dotenv()

# --- Конфигурация и Логирование ---

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
# Снижаем уровень логирования для сетевых библиотек, чтобы уменьшить шум
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

# --- Настройка Сетевого Таймаута ---
# Устанавливаем таймаут 20 секунд (вместо стандартных ~5 секунд)
# Это должно решить проблему с TimedOut.
CUSTOM_REQUEST = Request(
    connect_timeout=20.0,
    read_timeout=20.0,
    write_timeout=20.0,
)

# --- Настройка Базы Данных ---

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_USER = os.getenv("POSTGRES_USER", "user")
    DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")
    DB_NAME = os.getenv("POSTGRES_DB", "mydb")
    # Используем имя сервиса 'db' из docker-compose для хоста
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@db:5432/{DB_NAME}"
    logging.info(f"Используется DATABASE_URL по умолчанию: {DATABASE_URL}")

database = Database(DATABASE_URL)
last_status = {"status": "Система запущена"} # Глобальный статус для команды /status

async def initialize_database():
    """Подключение к БД и создание таблицы."""
    logging.info("Инициализация базы данных: Подключение...")

    try:
        await database.connect()
    except Exception as e:
        logging.critical(f"❌ Ошибка подключения к БД: {e}")
        raise ConnectionError(f"Не удалось подключиться к базе данных: {e}")

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
    logging.info("База данных готова. Таблица 'user_data' создана.")


# --- Обработчики Команд ---

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    if update.effective_chat:
        welcome_message = "Добро пожаловать! Я Telegram бот, готовый сохранять данные в PostgreSQL."
        await update.effective_chat.send_message(welcome_message)

async def save_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает /save <данные>: сохраняет данные в БД."""
    global last_status

    if not update.effective_chat or not update.effective_user:
        return

    if not context.args:
        await update.effective_chat.send_message("❌ Ошибка: Введите данные. Пример: /save Мои данные")
        return

    data_to_save = " ".join(context.args)
    chat_id = update.effective_chat.id
    username = update.effective_user.username if update.effective_user.username else "N/A"

    INSERT_QUERY = """
    INSERT INTO user_data (chat_id, username, data_text) VALUES (:chat_id, :username, :data_text)
    """

    values = {"chat_id": chat_id, "username": username, "data_text": data_to_save}

    try:
        await database.execute(query=INSERT_QUERY, values=values)

        last_status = {"status": "Успешно отправлено и сохранено", "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

        # Здесь произошел ваш TimedOut
        await update.effective_chat.send_message("✅ Успешно отправлено и сохранено!")
        logging.info(f"💾 Данные сохранены (Chat ID: {chat_id}): {data_to_save}")

    except Exception as e:
        logging.error(f"❌ Ошибка сохранения в БД или отправки ответа: {e}", exc_info=True)
        # Если ответ не отправляется, пытаемся отправить упрощенный
        try:
            await update.effective_chat.send_message(f"❌ Ошибка: При сохранении данных произошла ошибка.")
        except:
            pass # Если и это не сработало, просто логируем.


async def fetch_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает /fetch: возвращает последние 5 записей из БД."""
    if not update.effective_chat:
        return

    SELECT_QUERY = """
    SELECT id, data_text, created_at FROM user_data
    ORDER BY created_at DESC
    LIMIT 5;
    """

    try:
        records = await database.fetch_all(query=SELECT_QUERY)

        if not records:
            await update.effective_chat.send_message("❌ В базе данных нет записей.")
            return

        response_lines = ["🔍 Последние 5 записей:"]

        for record in records:
            time_str = record['created_at'].strftime("%Y-%m-%d %H:%M:%S")
            line = f"ID: {record['id']}, Текст: {record['data_text']}, Время: {time_str}"
            response_lines.append(line)

        # Здесь произошел ваш TimedOut
        await update.effective_chat.send_message("\n".join(response_lines))

    except Exception as e:
        logging.error(f"❌ Ошибка извлечения из БД или отправки ответа: {e}", exc_info=True)
        try:
            await update.effective_chat.send_message(f"❌ Ошибка: При получении данных произошла ошибка.")
        except:
            pass


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает /status: возвращает JSON-статус."""
    global last_status
    if not update.effective_chat:
        return

    db_status = "Connected" if database.is_connected else "Disconnected"

    current_status = last_status.copy()
    current_status['db_connection'] = db_status

    response_json = json.dumps(current_status, ensure_ascii=False, indent=2)

    message = f"**Статус данных:**\n```json\n{response_json}\n```"
    await update.effective_chat.send_message(message, parse_mode='Markdown')


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отвечает пользователю тем же текстом."""
    if update.effective_chat and update.effective_message.text and not update.effective_message.text.startswith('/'):
        await update.effective_chat.send_message(f"Вы сказали: {update.effective_message.text}")

# --- Инициализация Telegram Application ---

application: Application = None

def setup_bot() -> Application:
    """
    Создает и настраивает объект Application, используя увеличенный таймаут.
    """
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        logging.critical("TELEGRAM_BOT_TOKEN не найден. Приложение не может быть инициализировано.")
        raise ValueError("TELEGRAM_BOT_TOKEN не найден в переменных окружения.")

    app = (
        Application.builder()
        .token(token)
        .updater(None)
        .http_version("1.1")
        .request(CUSTOM_REQUEST) # FIX: Инъекция пользовательского объекта Request с таймаутом 20с
        .build()
    )

    # Добавление обработчиков команд
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("save", save_command))
    app.add_handler(CommandHandler("fetch", fetch_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    return app

# --- FastAPI Приложение ---

start_app = FastAPI(title="Telegram Bot Webhook Receiver")

@start_app.on_event("startup")
async def startup_event():
    global application
    # Инициализация БД и подключение
    try:
        await initialize_database()
    except ConnectionError:
        logging.critical("Невозможно продолжить без подключения к БД.")
        return

    # Инициализация Telegram Application
    application = setup_bot()
    await application.initialize()

    logging.info("🔥 Приложение запущено. Бот готов принимать обновления на /webhook.")


@start_app.on_event("shutdown")
async def shutdown_event():
    logging.info("Завершение работы приложения: Отключение от БД...")
    if database.is_connected:
        await database.disconnect()


@start_app.get("/")
async def health_check():
    return {"status": "ok", "message": "Бот активен и ждет обновлений на /webhook"}


@start_app.post("/webhook")
async def telegram_webhook(request: FastAPIRequest):
    global application
    if not application:
        logging.error("Telegram Application не инициализирован.")
        return JSONResponse(status_code=200, content={"status": "error", "message": "Service not ready"})

    try:
        body = await request.json()
        update = Update.de_json(body, application.bot)
        await application.process_update(update)
        # Всегда возвращаем 200 OK быстро
        return JSONResponse(status_code=200, content={"status": "ok"})

    except Exception as e:
        logging.error(f"❌ Ошибка при обработке вебхука: {e}", exc_info=True)
        return JSONResponse(status_code=200, content={"status": "internal_error", "message": "Update processed with error."})

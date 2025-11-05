# Python 3.12-slim негізгі имиджі
# 'slim' нұсқасы имидждің көлемін кішірейту үшін қолданылады.
FROM python:3.12-slim

# Жұмыс каталогын орнату
# Контейнер ішіндегі барлық операциялар осы каталогтан басталады
WORKDIR /app

# Тәуелділіктер файлын көшіру
# Бұл қадам имидж кэшін тиімді пайдалануға мүмкіндік береді
COPY requirements.txt .

# Тәуелділіктерді (Flask, SQLAlchemy, psycopg2, gunicorn) орнату
# --no-cache-dir имидж көлемін азайтады
RUN pip install --no-cache-dir -r requirements.txt

# Қосымшаның қалған файлдарын (bot_app.py, database.py, .env) көшіру
# .env файлы `docker-compose.yml` арқылы жүктеледі
COPY . .

# Flask қосымшасы жұмыс істейтін 5000 портын ашу
EXPOSE 5000

# Контейнерді іске қосу командасы
# Бұл команданы `docker-compose.yml` ішіндегі 'command' өрісінде Gunicorn арқылы анықтаймыз.
# Дегенмен, қауіпсіздік үшін мұнда CMD қалдыруға болады.
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "bot_app:app"]

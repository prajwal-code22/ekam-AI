FROM python:3.12-slim

# ffmpeg converts browser audio (WebM/MP4) to WAV for Gemini.
RUN apt-get update && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    DATABASE_PATH=/tmp/db.sqlite3

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

# Cloud Run sets $PORT. The demo DB is rebuilt and re-seeded on every start.
CMD ["sh", "-c", "python manage.py migrate --noinput && python manage.py seed_workers && exec gunicorn ekaam.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --timeout 120"]

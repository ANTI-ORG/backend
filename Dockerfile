# Используем официальный образ Python как базовый
FROM python:3.12.4-slim

# Устанавливаем рабочую директорию в корневую папку проекта
WORKDIR /app

# Копируем файлы зависимостей и конфигурации в контейнер
COPY requirements.txt /app/requirements.txt
COPY alembic.ini /app/alembic.ini
COPY app/fixtures.py /app/fixtures.py
COPY app /app/app/
COPY admin /app/admin/
COPY alembic /app/alembic/
COPY s3_manager /app/s3_manager/
COPY authentication /app/authentication/
COPY static /app/static/

# Устанавливаем зависимости
RUN pip install -r /app/requirements.txt

# Команда для запуска приложения с предварительным выполнением миграций и скрипта для заполнения базы данных
CMD alembic upgrade head && python /app/fixtures.py && uvicorn app.main:app --proxy-headers --forwarded-allow-ips="*" --host 0.0.0.0 --port $PORT

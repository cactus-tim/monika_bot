# --- Базовый образ
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Системные зависимости (минимум)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

# Копируем только зависимости для кэширования слоя
# В проекте файл назван "requirmetns.txt" — используем его как есть
COPY requirmetns.txt /app/requirements.txt
RUN pip install --upgrade pip && pip install -r /app/requirements.txt

# Копируем исходники
COPY . /app

# На всякий случай: локаль/таймзона (опционально)
ENV TZ=UTC

# Команда запуска (polling)
CMD ["python", "main.py"]
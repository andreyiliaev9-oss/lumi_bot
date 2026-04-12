FROM python:3.11-slim
WORKDIR /app
# Установка зависимостей
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*
# Копирование requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
# Копирование кода
COPY . .
# Создание директорий для данных
RUN mkdir -p /app/data /app/logs
# Запуск
CMD ["python", "bot.py"]

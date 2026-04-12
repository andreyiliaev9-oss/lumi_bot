#!/bin/bash
# Скрипт для запуска ЛЮМИ БОТ
echo "🚀 Запуск ЛЮМИ БОТ..."
# Проверка наличия .env
if [ ! -f .env ]; then
    echo "⚠️  Файл .env не найден!"
    echo "Создаю из .env.example..."
    cp .env.example .env
    echo "❌ Пожалуйста, отредактируй .env и укажи BOT_TOKEN"
    exit 1
fi
# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не установлен"
    exit 1
fi
# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "📦 Создание виртуального окружения..."
    python3 -m venv venv
fi
# Активация venv
echo "🔄 Активация окружения..."
source venv/bin/activate
# Установка зависимостей
echo "📥 Установка зависимостей..."
pip install -q -r requirements.txt
# Запуск бота
echo "🤖 Запуск бота..."
echo "Нажми Ctrl+C для остановки"
echo ""
python3 bot.py

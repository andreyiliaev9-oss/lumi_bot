@echo off
chcp 65001 >nul
cls
echo 🚀 Запуск ЛЮМИ БОТ...
:: Проверка наличия .env
if not exist .env (
    echo ⚠️  Файл .env не найден!
    echo Создаю из .env.example...
    copy .env.example .env
    echo ❌ Пожалуйста, отредактируй .env и укажи BOT_TOKEN
    pause
    exit /b 1
)
:: Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python не установлен
    pause
    exit /b 1
)
:: Проверка виртуального окружения
if not exist venv (
    echo 📦 Создание виртуального окружения...
    python -m venv venv
)
:: Активация venv
echo 🔄 Активация окружения...
call venv\Scripts\activate.bat
:: Установка зависимостей
echo 📥 Установка зависимостей...
pip install -q -r requirements.txt
:: Запуск бота
echo 🤖 Запуск бота...
echo Нажми Ctrl+C для остановки
echo.
python bot.py
pause

import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from db.db import init_db
from handlers import start, profile, admin, private, cycle, diary

# Настройка логирования, чтобы видеть ошибки в консоли
logging.basicConfig(level=logging.INFO)

async def main():
    # 1. Инициализация базы данных (создание таблиц)
    await init_db()
    
    # 2. Создание бота и диспетчера
    # Используем DefaultBotProperties для настройки ParseMode (в новых версиях aiogram)
    from aiogram.client.default import DefaultBotProperties
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # 3. Регистрация всех наших модулей (Роутеров)
    # Порядок важен: админку и приватки ставим в начало
    dp.include_routers(
        admin.router,
        start.router,
        profile.router,
        private.router,
        cycle.router,
        diary.router
    )

    # 4. Запуск бота (удаляем старые сообщения, которые пришли пока бот лежал)
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🚀 БОТ ЛЮМИ УСПЕШНО ЗАПУЩЕН!")
    print("👑 Админ-панель доступна владельцу.")
    
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Бот остановлен!")

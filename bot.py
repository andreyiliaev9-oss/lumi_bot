import asyncio
import logging
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN
from db.database import init_db

# Импортируем наш роутер (обработчик /start)
from handlers.start import router as start_router

# Включаем логирование, чтобы видеть в консоли, что происходит
logging.basicConfig(level=logging.INFO)

# Создаем объекты бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# "Приклеиваем" наш обработчик к диспетчеру
dp.include_router(start_router)


async def main():
    # 1. Инициализируем базу данных (создаст таблицы при первом запуске)
    await init_db()
    print("✅ База данных успешно подключена!")
    
    # 2. Удаляем старые вебхуки (чтобы бот точно работал в режиме опроса)
    await bot.delete_webhook(drop_pending_updates=True)
    print("🚀 Бот ЛЮМИ успешно запущен и готов к работе!")
    
    # 3. Запускаем постоянный опрос Telegram-серверов
    await dp.start_polling(bot)


if __name__ == "__main__":
    # Обертка для правильной работы асинхронности
    asyncio.run(main())

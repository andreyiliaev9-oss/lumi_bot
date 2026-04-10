import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from handlers import register_all_handlers
from db.db import init_db
from services.scheduler import setup_scheduler
from config import BOT_TOKEN

logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
    dp = Dispatcher()
    await init_db()
    register_all_handlers(dp)
    await setup_scheduler(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

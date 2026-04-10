import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiosqlite

from db.database import init_db, DB_NAME

API_TOKEN = '8690428738:AAGUuo-V3id99Z-3UsT6twy2bJGmScCXFbA'
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# Функция рассылки
async def send_scheduled_messages(mode):
    async with aiosqlite.connect(DB_NAME) as db:
        # Ищем пользователей, у которых включено уведомление
        column_enabled = "morning_enabled" if mode == "morning" else "evening_enabled"
        column_time = "morning_time" if mode == "morning" else "evening_time"
        column_msg = "morning_msg" if mode == "morning" else "evening_msg"
        
        current_time = datetime.now().strftime("%H:%M")
        
        async with db.execute(f"SELECT user_id, {column_msg} FROM users WHERE {column_enabled} = 1 AND {column_time} = ?", (current_time,)) as cursor:
            users = await cursor.fetchall()
            for user_id, msg in users:
                try:
                    await bot.send_message(user_id, msg)
                except Exception as e:
                    print(f"Ошибка отправки пользователю {user_id}: {e}")

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.from_user.first_name)
        )
        await db.commit()
    await message.answer("Добро пожаловать в ЛЮМИ. Твой персональный помощник запущен.")

async def main():
    await init_db()
    
    # Запускаем проверку каждую минуту
    scheduler.add_job(send_scheduled_messages, "interval", minutes=1, args=["morning"])
    scheduler.add_job(send_scheduled_messages, "interval", minutes=1, args=["evening"])
    scheduler.start()
    
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

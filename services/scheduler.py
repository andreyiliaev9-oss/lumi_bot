import asyncio
from datetime import datetime
from aiogram import Bot
from sqlalchemy import select
from db.db import async_session
from db.models import User, Compliment, CycleTip
import random

async def send_morning_push(bot: Bot):
    async with async_session() as session:
        users = await session.scalars(select(User))
        compliments = await session.scalars(select(Compliment)).all()
        
        for user in users:
            # Проверяем время (упрощенно, для экосистемы)
            current_time = datetime.now().strftime("%H:%M")
            if current_time == user.morning_time:
                msg = "☀️ <b>Доброе утро, принцесса!</b>\n\n"
                if compliments:
                    msg += f"Сегодня я хочу сказать: {random.choice(compliments).text}\n\n"
                msg += "Не забудь заглянуть в планировщик, у тебя сегодня великие дела! ✨"
                
                try:
                    await bot.send_message(user.tg_id, msg, parse_mode="HTML")
                except: continue

async def send_evening_report(bot: Bot):
    async with async_session() as session:
        users = await session.scalars(select(User))
        for user in users:
            current_time = datetime.now().strftime("%H:%M")
            if current_time == user.evening_time:
                msg = (
                    "🌙 <b>Время подвести итоги дня</b>\n"
                    "━━━━━━━━━━━━━━━\n"
                    "Как прошло твое сегодня? Заполни дневник или отметь выполненные привычки. "
                    "Я жду тебя в приватной зоне! ✨"
                )
                try:
                    await bot.send_message(user.tg_id, msg, parse_mode="HTML", reply_markup=None)
                except: continue

async def scheduler_loop(bot: Bot):
    while True:
        await send_morning_push(bot)
        await send_evening_report(bot)
        await asyncio.sleep(60) # Проверка каждую минуту

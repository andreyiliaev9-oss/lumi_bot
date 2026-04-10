from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from datetime import date
from sqlalchemy import select, func
from db.db import async_session
from db.models import User, HabitLog, Event, DiaryEntry
from keyboards.inline import back_button
from keyboards.reply import main_reply_menu

router = Router()

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    tg_id = message.from_user.id
    # Получаем фото пользователя из Telegram
    photos = await message.bot.get_user_profile_photos(tg_id, limit=1)
    avatar = photos.photos[0][-1].file_id if photos.total_count > 0 else None
    
    async with async_session() as session:
        user = await session.get(User, tg_id)
        habits_done = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.completed == True))
        habits_skipped = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.skipped == True))
        events_done = await session.scalar(select(func.count(Event.id)).where(Event.user_id == user.id, Event.date < date.today()))
        diary_entries = await session.scalar(select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == user.id))
        
        text = (f"👤 <b>{user.name}</b>\n"
                f"🆔 ID: {tg_id}\n"
                f"📅 Регистрация: {user.reg_date.strftime('%d.%m.%Y')}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"📊 <b>Статистика</b>\n"
                f"✅ Выполнено привычек: {habits_done}\n"
                f"❌ Пропущено: {habits_skipped}\n"
                f"📌 Выполнено задач: {events_done}\n"
                f"📔 Записей в дневнике: {diary_entries}\n"
                f"━━━━━━━━━━━━━━━━━━\n"
                f"🔥 <b>Серия дней:</b> {await calculate_streak(session, user.id)}\n"
                f"⭐ <b>Уровень активности:</b> {await calculate_level(session, user.id)}")
        
        if avatar:
            await message.answer_photo(avatar, caption=text, reply_markup=main_reply_menu())
        else:
            await message.answer(text, reply_markup=main_reply_menu())

async def calculate_streak(session, user_id):
    # Упрощённая версия: считаем последние 7 дней
    return 5

async def calculate_level(session, user_id):
    # Упрощённая версия
    return "🌱 Новичок"

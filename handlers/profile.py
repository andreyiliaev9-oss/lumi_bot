from aiogram import Router, F
from aiogram.types import Message
from datetime import date, timedelta
from sqlalchemy import select, func
from db.db import async_session
from db.models import User, HabitLog, Event, DiaryEntry, CycleLog
from keyboards.reply import main_reply_menu

router = Router()

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    tg_id = message.from_user.id

    avatar = None
    try:
        photos = await message.bot.get_user_profile_photos(tg_id, limit=1)
        if photos.total_count > 0:
            avatar = photos.photos[0][-1].file_id
    except:
        pass

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            await message.answer("Ошибка: пользователь не найден")
            return

        habits_done = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.completed == True))
        habits_skipped = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.skipped == True))
        events_done = await session.scalar(select(func.count(Event.id)).where(Event.user_id == user.id, Event.date < date.today()))
        diary_entries = await session.scalar(select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == user.id))

        streak = 0
        current = date.today()
        while True:
            habit = await session.scalar(select(HabitLog).where(HabitLog.user_id == user.id, HabitLog.date == current, HabitLog.completed == True))
            cycle = await session.scalar(select(CycleLog).where(CycleLog.user_id == user.id, CycleLog.date == current))
            if habit or cycle:
                streak += 1
                current -= timedelta(days=1)
            else:
                break

        text = (
            f"<b>👤 {user.name}</b>\n"
            f"🆔 ID: {tg_id}\n"
            f"📅 Регистрация: {user.reg_date.strftime('%d.%m.%Y')}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"📊 <b>Статистика</b>\n"
            f"✅ Выполнено привычек: {habits_done or 0}\n"
            f"❌ Пропущено: {habits_skipped or 0}\n"
            f"📌 Выполнено задач: {events_done or 0}\n"
            f"📔 Записей в дневнике: {diary_entries or 0}\n"
            f"━━━━━━━━━━━━━━━━━━\n"
            f"🔥 Серия дней: {streak}\n"
            f"⭐ Уровень активности: 🌱 Новичок"
        )

        if avatar:
            await message.answer_photo(avatar, caption=text, reply_markup=main_reply_menu())
        else:
            await message.answer(text, reply_markup=main_reply_menu())

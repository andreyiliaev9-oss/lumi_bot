from aiogram import Router, F
from aiogram.types import CallbackQuery
from datetime import date
from sqlalchemy import select, func
from db.db import async_session
from db.models import User, HabitLog, Event, DiaryEntry
from keyboards.inline import back_button

router = Router()

@router.callback_query(F.data == "profile")
async def show_profile(callback: CallbackQuery):
    tg_id = callback.from_user.id
    async with async_session() as session:
        user = await session.get(User, tg_id)
        habits_done = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.completed == True))
        habits_skipped = await session.scalar(select(func.count(HabitLog.id)).where(HabitLog.user_id == user.id, HabitLog.skipped == True))
        events_done = await session.scalar(select(func.count(Event.id)).where(Event.user_id == user.id, Event.date < date.today()))
        diary_entries = await session.scalar(select(func.count(DiaryEntry.id)).where(DiaryEntry.user_id == user.id))
        text = (f"👤 <b>{user.name}</b>\n"
                f"📅 Регистрация: {user.reg_date.strftime('%d.%m.%Y')}\n"
                f"✅ Выполнено привычек: {habits_done}\n"
                f"❌ Пропущено: {habits_skipped}\n"
                f"📌 Выполнено задач: {events_done}\n"
                f"📔 Записей в дневнике: {diary_entries}")
        await callback.message.edit_text(text, reply_markup=back_button("start"))
    await callback.answer()

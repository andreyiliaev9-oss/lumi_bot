from aiogram import Router, F
from aiogram.types import Message
from db.db import async_session
from db.models import User
from sqlalchemy import select

router = Router()

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if not user:
            return await message.answer("Профиль не найден. Напиши /start для регистрации.")

        # Собираем текст профиля
        profile_text = (
            f"👤 <b>ПРОФИЛЬ</b>\n\n"
            f"Приятно видеть тебя, <b>{user.name}</b>!\n"
            f"🆔 ID: <code>{user.tg_id}</code>\n\n"
            f"<b>Твои успехи:</b>\n"
            f"✨ Выполнено привычек: <b>{user.completed_habits}</b>\n"
            f"📝 Записей в дневнике: <b>{user.diary_count}</b>\n"
            f"🔥 Выполнено задач: <b>{user.completed_tasks}</b>\n\n"
            f"<b>Состояние:</b>\n"
            f"🎭 Эмоция недели: <b>Задумчивость 🤔</b>\n" # Позже сделаем расчет
            f"🌸 Цикл: <b>{user.cycle_length}-й день</b>\n\n"
            f"<i>С Люми с {user.reg_date.strftime('%d.%m.%Y')}</i> 💜"
        )

        # Пытаемся получить фото профиля
        photos = await message.from_user.get_profile_photos(limit=1)
        if photos.total_count > 0:
            await message.answer_photo(
                photo=photos.photos[0][-1].file_id,
                caption=profile_text,
                parse_mode="HTML"
            )
        else:
            await message.answer(profile_text, parse_mode="HTML")

from aiogram import Router, F
from aiogram.types import Message
from db.db import async_session
from db.models import User
from sqlalchemy import select

router = Router()

@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    async with async_session() as session:
        # Ищем пользователя в базе
        result = await session.execute(
            select(User).where(User.tg_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            return await message.answer("Профиль не найден. Пожалуйста, напиши /start.")

        # Форматируем дату регистрации
        reg_date_str = user.reg_date.strftime("%d.%m.%Y")
        
        # Собираем текст профиля по ТЗ
        profile_text = (
            f"👤 <b>ВАШ ПРОФИЛЬ</b>\n"
            f"━━━━━━━━━━━━━━\n\n"
            f"✨ <b>Имя:</b> {user.name}\n"
            f"🆔 <b>Твой ID:</b> <code>{user.tg_id}</code>\n"
            f"📅 <b>С ЛЮМИ с:</b> {reg_date_str}\n\n"
            f"<b>Твои успехи:</b>\n"
            f"📝 Записей в дневнике: <b>{user.diary_count}</b>\n"
            f"🔥 Выполнено задач: <b>{user.completed_tasks}</b>\n"
            f"✅ Полезных привычек: <b>{user.completed_habits}</b>\n\n"
            f"━━━━━━━━━━━━━━\n"
            f"<i>«Маленькими шагами к большим целям...»</i>"
        )

        # Пытаемся получить аватарку пользователя
        try:
            photos = await message.from_user.get_profile_photos(limit=1)
            if photos.total_count > 0:
                # Если фото есть, отправляем его с подписью
                await message.answer_photo(
                    photo=photos.photos[0][-1].file_id,
                    caption=profile_text,
                    parse_mode="HTML"
                )
            else:
                # Если фото нет, просто текст
                await message.answer(profile_text, parse_mode="HTML")
        except Exception:
            # На случай ошибки доступа к фото — шлем текст
            await message.answer(profile_text, parse_mode="HTML")

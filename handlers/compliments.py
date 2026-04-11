from aiogram import Router, F
from aiogram.types import Message
from db.db import async_session
from db.models import Compliment
from sqlalchemy import select, func

router = Router()

@router.message(F.text == "✨ Комплименты")
async def send_compliment(message: Message):
    async with async_session() as session:
        # Ищем случайный активный комплимент в базе
        stmt = select(Compliment).where(Compliment.is_active == True).order_by(func.random()).limit(1)
        result = await session.execute(stmt)
        compliment = result.scalar_one_or_none()

        if compliment:
            await message.answer(f"✨ {compliment.text}")
        else:
            # Если база пустая, даем временный ответ
            await message.answer("Ты сегодня выглядишь просто чудесно! 💜\n\n<i>(Админ еще не заполнил базу комплиментов)</i>", parse_mode="HTML")

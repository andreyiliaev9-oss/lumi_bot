from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy import select
from db.models import User
from db.database import async_session
from keyboards.reply import main_kb

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.user_id == message.from_user.id))
        if not user:
            # Если пользователя нет, можно добавить логику регистрации позже
            await message.answer("Добро пожаловать! Используйте меню для навигации.", reply_markup=main_kb())
        else:
            await message.answer("С возвращением!", reply_markup=main_kb())

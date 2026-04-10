from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from db.db import async_session
from db.models import User
from keyboards.inline import main_menu

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        user = await session.get(User, tg_id)
        if not user:
            user = User(tg_id=tg_id, name=message.from_user.full_name)
            session.add(user)
            await session.commit()
            await message.answer(f"Привет, {user.name}! Я ЛЮМИ – твой личный помощник.", reply_markup=main_menu())
        else:
            await message.answer(f"С возвращением, {user.name}!", reply_markup=main_menu())

@router.callback_query(F.data == "start")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=main_menu())
    await callback.answer()

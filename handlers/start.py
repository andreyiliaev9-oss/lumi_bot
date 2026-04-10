from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from sqlalchemy import select
from db.db import async_session
from db.models import User
from keyboards.reply import main_reply_menu
from keyboards.inline import back_button

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        result = await session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(tg_id=tg_id, name=message.from_user.full_name)
            session.add(user)
            await session.commit()
            await message.answer(
                f"Привет, {user.name}! Я ЛЮМИ – твой личный помощник.",
                reply_markup=main_reply_menu()
            )
        else:
            await message.answer(
                f"С возвращением, {user.name}!",
                reply_markup=main_reply_menu()
            )

@router.callback_query(F.data == "start")
async def back_to_menu(callback: CallbackQuery):
    await callback.message.edit_text("Главное меню:", reply_markup=back_button("start"))
    await callback.answer()

 from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import async_session
from db.models import User
from sqlalchemy import select
from keyboards.reply import main_kb
from config import ADMIN_ID

router = Router()

class Registration(StatesGroup):
    waiting_for_name = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session() as session:
        # Проверяем, есть ли пользователь в базе
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        
        if user:
            # Если уже есть — просто приветствуем
            await message.answer(
                f"Рада снова тебя видеть, <b>{user.name}</b>! 💜\nЧем займемся сегодня?",
                reply_markup=main_kb(message.from_user.id, ADMIN_ID),
                parse_mode="HTML"
            )
        else:
            # Если нет — начинаем знакомство
            await message.answer(
                "Привет! 🎆 Я <b>ЛЮМИ</b>, твой персональный ассистент.\n"
                "Давай познакомимся. Как мне к тебе обращаться?",
                parse_mode="HTML"
            )
            await state.set_state(Registration.waiting_for_name)

@router.message(Registration.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text
    
    async with async_session() as session:
        new_user = User(
            tg_id=message.from_user.id,
            name=name
        )
        session.add(new_user)
        await session.commit()
    
    await state.clear()
    await message.answer(
        f"Приятно познакомиться, <b>{name}</b>! ✨\n"
        "Я создала твой профиль. Теперь тебе доступны все мои функции.",
        reply_markup=main_kb(message.from_user.id, ADMIN_ID),
        parse_mode="HTML"
    )

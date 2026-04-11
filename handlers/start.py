 from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import async_session
from db.models import User
from sqlalchemy import select
from keyboards.reply import main_kb

router = Router()

# Состояние для регистрации
class Registration(StatesGroup):
    waiting_for_name = State()

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    async with async_session() as session:
        # Проверяем, есть ли пользователь в нашей новой базе
        result = await session.execute(select(User).where(User.tg_id == message.from_user.id))
        user = result.scalar_one_or_none()
        
        if user:
            # Если уже зарегистрирован — просто приветствуем и даем меню
            await message.answer(
                f"Рада снова тебя видеть, <b>{user.name}</b>! ✨\nЧем займёмся сегодня?",
                reply_markup=main_kb(message.from_user.id),
                parse_mode="HTML"
            )
        else:
            # Если новичок — запускаем процесс знакомства
            await message.answer(
                "Привет! ✨ Я <b>ЛЮМИ</b>, твой персональный ассистент.\n"
                "Давай познакомимся. Как мне к тебе обращаться?",
                parse_mode="HTML"
            )
            await state.set_state(Registration.waiting_for_name)

@router.message(Registration.waiting_for_name)
async def get_name(message: Message, state: FSMContext):
    name = message.text.strip()
    
    if len(name) < 2 or len(name) > 20:
        return await message.answer("Пожалуйста, введи корректное имя (от 2 до 20 символов).")

    async with async_session() as session:
        # Создаем нового пользователя в базе
        new_user = User(
            tg_id=message.from_user.id,
            name=name
        )
        session.add(new_user)
        await session.commit()
    
    await state.clear()
    await message.answer(
        f"Приятно познакомиться, <b>{name}</b>! 💜\n"
        "Я создала твой профиль. Теперь тебе доступны все мои функции.",
        reply_markup=main_kb(message.from_user.id),
        parse_mode="HTML"
    )

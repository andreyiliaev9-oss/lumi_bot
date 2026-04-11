import hashlib
import time
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db.db import async_session
from db.models import User
from keyboards.inline import private_menu, back_button
from keyboards.reply import main_reply_menu

router = Router()

# Временное хранилище блокировок
blocked_until = {}

class PrivateAuthState(StatesGroup):
    waiting_pin = State()

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

async def get_user_pin_hash(user_id: int) -> str:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        return user.private_pin_hash if user else None

async def set_user_pin_hash(user_id: int, pin_hash: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if user:
            user.private_pin_hash = pin_hash
            await session.commit()

async def set_private_session(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if user:
            user.private_session_expires = datetime.now() + timedelta(hours=1)
            await session.commit()

async def is_private_session_valid(user_id: int) -> bool:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if user and user.private_session_expires:
            return user.private_session_expires > datetime.now()
    return False

async def clear_private_session(user_id: int):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        if user:
            user.private_session_expires = None
            await session.commit()

@router.message(F.text == "🔒 Приватное")
async def private_auth_start(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # Проверка блокировки
    if user_id in blocked_until and blocked_until[user_id] > time.time():
        remaining = int(blocked_until[user_id] - time.time())
        await message.answer(f"⛔ Доступ заблокирован на {remaining} секунд. Попробуйте позже.")
        return
    # Если уже есть активная сессия
    if await is_private_session_valid(user_id):
        await message.answer("🔓 Вы уже авторизованы в приватной зоне.", reply_markup=private_menu())
        return
    # Проверяем, установлен ли PIN
    pin_hash = await get_user_pin_hash(user_id)
    if pin_hash is None:
        await message.answer("🔐 Добро пожаловать в приватную зону!\nУстановите PIN-код (4 цифры):")
        await state.set_state(PrivateAuthState.waiting_pin)
        await state.update_data(is_setup=True)
    else:
        await message.answer("🔒 Введите PIN-код для доступа в приватную зону:")
        await state.set_state(PrivateAuthState.waiting_pin)
        await state.update_data(is_setup=False)

@router.message(PrivateAuthState.waiting_pin)
async def process_pin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    pin = message.text.strip()
    await message.delete()  # удаляем сообщение с PIN
    data = await state.get_data()
    is_setup = data.get('is_setup', False)
    if is_setup:
        # Установка PIN
        if len(pin) != 4 or not pin.isdigit():
            await message.answer("❌ PIN должен состоять из 4 цифр. Попробуйте ещё раз.")
            return
        pin_hash = hash_pin(pin)
        await set_user_pin_hash(user_id, pin_hash)
        await set_private_session(user_id)
        await message.answer("✅ PIN установлен! Добро пожаловать в приватную зону.", reply_markup=private_menu())
        await state.clear()
    else:
        # Проверка PIN
        if user_id in blocked_until and blocked_until[user_id] > time.time():
            remaining = int(blocked_until[user_id] - time.time())
            await message.answer(f"⛔ Доступ заблокирован на {remaining} секунд.")
            await state.clear()
            return
        correct_hash = await get_user_pin_hash(user_id)
        if hash_pin(pin) == correct_hash:
            await set_private_session(user_id)
            await message.answer("✅ Доступ разрешён.", reply_markup=private_menu())
            await state.clear()
        else:
            # Неверный PIN
            attempts = data.get('attempts', 0) + 1
            await state.update_data(attempts=attempts)
            if attempts >= 3:
                blocked_until[user_id] = time.time() + 300  # 5 минут
                await message.answer("⛔ Неверный PIN 3 раза. Доступ заблокирован на 5 минут.")
                await state.clear()
            else:
                await message.answer(f"❌ Неверный PIN. Осталось попыток: {3 - attempts}")
                # Оставляем состояние, чтобы можно было ввести ещё раз

@router.callback_query(F.data == "exit_private")
async def exit_private(callback: CallbackQuery):
    user_id = callback.from_user.id
    await clear_private_session(user_id)
    await callback.message.edit_text("Вы вышли из приватной зоны.")
    is_admin = (user_id == 8666952157)
    await callback.message.answer("Главное меню:", reply_markup=main_reply_menu(is_admin=is_admin))
    await callback.answer()

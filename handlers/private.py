import hashlib
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from db.db import async_session
from db.models import User
from sqlalchemy import select, update
from keyboards.inline import pin_keyboard, private_main_menu_kb

router = Router()

# Временное хранилище попыток и текущего ввода (чтобы не дергать базу на каждую цифру)
attempts = {} # {tg_id: count}
lockouts = {} # {tg_id: end_time}
current_inputs = {} # {tg_id: "123"}

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

@router.message(F.text == "🔐 Приватное")
async def enter_private(message: Message):
    user_id = message.from_user.id
    
    # Проверка на блокировку
    if user_id in lockouts:
        if datetime.now() < lockouts[user_id]:
            remains = int((lockouts[user_id] - datetime.now()).total_seconds() / 60)
            return await message.answer(f"❌ Доступ заблокирован. Попробуйте через {remains + 1} мин.")
        else:
            del lockouts[user_id]
            attempts[user_id] = 0

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        
        if not user.private_pin_hash:
            await message.answer("✨ <b>Установка защиты</b>\nПридумайте и введите 4-значный PIN-код:", 
                                 reply_markup=pin_keyboard(), parse_mode="HTML")
        else:
            await message.answer("🔐 <b>Доступ в приватную зону</b>\nВведите ваш PIN-код:", 
                                 reply_markup=pin_keyboard(), parse_mode="HTML")

@router.callback_query(F.data.startswith("pin_"))
async def process_pin(callback: CallbackQuery):
    user_id = callback.from_user.id
    action = callback.data.replace("pin_", "")
    
    if user_id not in current_inputs:
        current_inputs[user_id] = ""

    # Логика кнопок
    if action == "clear":
        current_inputs[user_id] = ""
    elif action == "backspace":
        current_inputs[user_id] = current_inputs[user_id][:-1]
    elif action == "none":
        await callback.answer()
        return
    else:
        if len(current_inputs[user_id]) < 4:
            current_inputs[user_id] += action

    # Если ввели 4 цифры — проверяем
    if len(current_inputs[user_id]) == 4:
        entered_pin = current_inputs[user_id]
        current_inputs[user_id] = "" # Сбрасываем ввод
        
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.tg_id == user_id))
            hashed_entered = hash_pin(entered_pin)

            # ПЕРВЫЙ ВХОД (Установка)
            if not user.private_pin_hash:
                await session.execute(update(User).where(User.tg_id == user_id).values(private_pin_hash=hashed_entered))
                await session.commit()
                await callback.message.edit_text("✅ <b>PIN-код установлен!</b>\nДобро пожаловать в приватную зону.", 
                                                 reply_markup=private_main_menu_kb(), parse_mode="HTML")
            
            # ПОВТОРНЫЙ ВХОД (Проверка)
            elif user.private_pin_hash == hashed_entered:
                attempts[user_id] = 0
                await callback.message.edit_text("🔓 <b>Доступ разрешен</b>\nВыберите раздел:", 
                                                 reply_markup=private_main_menu_kb(), parse_mode="HTML")
            else:
                # Ошибка ввода
                attempts[user_id] = attempts.get(user_id, 0) + 1
                if attempts[user_id] >= 3:
                    lockouts[user_id] = datetime.now() + timedelta(minutes=5)
                    await callback.message.edit_text("❌ <b>Трижды неверно!</b>\nДоступ заблокирован на 5 минут.")
                else:
                    await callback.answer(f"Неверный PIN! Осталось попыток: {3 - attempts[user_id]}", show_alert=True)
                    await callback.message.edit_reply_markup(reply_markup=pin_keyboard(""))
    else:
        # Просто обновляем точки на экране
        await callback.message.edit_reply_markup(reply_markup=pin_keyboard(current_inputs[user_id]))

@router.callback_query(F.data == "p_exit")
async def exit_private(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🚪 Вы вышли из приватной зоны. Доступ снова закрыт.")

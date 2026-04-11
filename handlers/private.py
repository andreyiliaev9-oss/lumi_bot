import hashlib
import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from db.db import async_session
from db.models import User
from sqlalchemy import select, update
from keyboards.inline import pin_keyboard, private_main_menu_kb

router = Router()

# Состояния для установки PIN
class PrivateStates(StatesGroup):
    setting_pin = State()
    confirming_pin = State()

# Временное хранилище для безопасности (сбрасывается при перезагрузке)
attempts = {}  # {user_id: count}
lockouts = {}  # {user_id: end_time}
current_inputs = {} # {user_id: "123"}

def hash_pin(pin: str) -> str:
    return hashlib.sha256(pin.encode()).hexdigest()

@router.message(F.text == "🔐 Приватное")
async def enter_private(message: Message, state: FSMContext):
    user_id = message.from_user.id
    
    # 1. Проверка блокировки
    if user_id in lockouts:
        if datetime.now() < lockouts[user_id]:
            remains = int((lockouts[user_id] - datetime.now()).total_seconds() / 60)
            return await message.answer(f"❌ Доступ временно заблокирован. Попробуйте через {remains + 1} мин.")
        else:
            del lockouts[user_id]
            attempts[user_id] = 0

    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_id))
        
        # 2. Если PIN еще не установлен
        if not user.private_pin_hash:
            await message.answer(
                "✨ <b>Установка защиты</b>\n\n"
                "Вы входите в приватную зону впервые. Придумайте 4-значный PIN-код и введите его на клавиатуре ниже:",
                reply_markup=pin_keyboard(), 
                parse_mode="HTML"
            )
        else:
            # 3. Обычный вход
            await message.answer(
                "🔐 <b>Доступ в приватную зону</b>\n\nВведите ваш секретный PIN-код:", 
                reply_markup=pin_keyboard(), 
                parse_mode="HTML"
            )

@router.callback_query(F.data.startswith("pin_"))
async def process_pin_input(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    action = callback.data.replace("pin_", "")
    
    if user_id not in current_inputs:
        current_inputs[user_id] = ""

    # Логика кнопок клавиатуры
    if action == "clear":
        current_inputs[user_id] = ""
    elif action == "backspace":
        current_inputs[user_id] = current_inputs[user_id][:-1]
    elif action == "none":
        return await callback.answer()
    else:
        if len(current_inputs[user_id]) < 4:
            current_inputs[user_id] += action

    # Если ввели 4 цифры — проверяем
    if len(current_inputs[user_id]) == 4:
        entered_pin = current_inputs[user_id]
        current_inputs[user_id] = "" # Сбрасываем для безопасности
        
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.tg_id == user_id))
            hashed_entered = hash_pin(entered_pin)

            # Установка нового PIN
            if not user.private_pin_hash:
                await session.execute(update(User).where(User.tg_id == user_id).values(private_pin_hash=hashed_entered))
                await session.commit()
                await callback.message.edit_text(
                    "✅ <b>Защита активирована!</b>\n\nТеперь ваша приватная зона под надежным замком.",
                    reply_markup=private_main_menu_kb(),
                    parse_mode="HTML"
                )
            
            # Проверка существующего PIN
            elif user.private_pin_hash == hashed_entered:
                attempts[user_id] = 0
                await callback.message.edit_text(
                    "🔓 <b>Доступ разрешен</b>\n\nДобро пожаловать в ваше личное пространство. Что откроем?", 
                    reply_markup=private_main_menu_kb(),
                    parse_mode="HTML"
                )
            else:
                # Неверный ввод
                attempts[user_id] = attempts.get(user_id, 0) + 1
                if attempts[user_id] >= 3:
                    lockouts[user_id] = datetime.now() + timedelta(minutes=5)
                    await callback.message.edit_text("❌ <b>Ошибка!</b>\nСлишком много неверных попыток. Доступ закрыт на 5 минут.")
                else:
                    await callback.answer(f"Неверный код! Осталось попыток: {3 - attempts[user_id]}", show_alert=True)
                    await callback.message.edit_reply_markup(reply_markup=pin_keyboard(""))
    else:
        # Обновляем визуальное отображение точек на клавиатуре
        await callback.message.edit_reply_markup(reply_markup=pin_keyboard(current_inputs[user_id]))

@router.callback_query(F.data == "p_exit")
async def exit_private_zone(callback: CallbackQuery):
    await callback.message.delete()
    await callback.message.answer("🚪 <b>Сейф закрыт.</b>\nВы вышли из приватной зоны.")

@router.callback_query(F.data == "p_main")
async def back_to_private_menu(callback: CallbackQuery):
    await callback.message.edit_text(
        "🔓 <b>Приватная зона</b>\n\nВыберите раздел:",
        reply_markup=private_main_menu_kb(),
        parse_mode="HTML"
    )

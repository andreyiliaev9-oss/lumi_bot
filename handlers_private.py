import asyncio
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import database as db
from config import settings
from keyboards import *
from states import PrivateStates
from handlers import main_menu_keyboard, get_user_data, clear_user_data
router = Router()
# Временное хранилище PIN-попыток
pin_attempts = {}
pin_block_until = {}
private_access = {}  # Словарь для отслеживания активных сессий приватного раздела
async def auto_logout(user_id: int, message: Message, state: FSMContext):
    """Автоматический выход через 5 минут бездействия"""
    await asyncio.sleep(settings.PRIVATE_AUTO_LOGOUT_MINUTES * 60)
    
    if user_id in private_access:
        del private_access[user_id]
        await state.clear()
        await message.answer(
            "🔒 Приватный раздел закрыт (автовыход по бездействию).",
            reply_markup=main_menu_keyboard()
        )
# ============== ЛИЧНОЕ (PIN) ==============
@router.message(F.text == "🔒 Личное")
async def private_section_entry(message: Message, state: FSMContext):
    """Вход в приватный раздел"""
    user = await db.get_user(message.from_user.id)
    
    # Проверка блокировки
    if user.pin_blocked_until and datetime.utcnow() < user.pin_blocked_until:
        remaining = int((user.pin_blocked_until - datetime.utcnow()).total_seconds() / 60)
        await message.answer(
            f"⛔ Доступ заблокирован.\n\n"
            f"Попробуй снова через {remaining} минут."
        )
        return
    
    # Проверка, установлен ли PIN
    if not user.pin_code:
        # Первый вход - нужно установить PIN
        await state.set_state(PrivateStates.waiting_pin_new)
        await message.answer(
            "🔐 <b>Первый вход в Личный раздел</b>\n\n"
            "Создай PIN-код (4 цифры):",
            reply_markup=pin_keyboard()
        )
        return
    
    # Ввод PIN
    await state.set_state(PrivateStates.waiting_pin_enter)
    get_user_data(message.from_user.id)["current_pin"] = ""
    
    await message.answer(
        "🔐 Введи PIN-код:\n\n"
        f"Введено: ____",
        reply_markup=pin_keyboard()
    )
@router.callback_query(F.data.startswith("pin_"), StateFilter(PrivateStates.waiting_pin_enter))
async def pin_digit_entered(callback: CallbackQuery, state: FSMContext):
    """Ввод цифры PIN"""
    action = callback.data.replace("pin_", "")
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    if action == "confirm":
        # Проверка PIN
        current_pin = user_data.get("current_pin", "")
        
        if len(current_pin) != 4:
            await callback.answer("Введите 4 цифры!")
            return
        
        user = await db.get_user(user_id)
        
        if current_pin == user.pin_code:
            # PIN верный
            user.pin_attempts = 0
            async with db.async_session() as session:
                await session.merge(user)
                await session.commit()
            
            private_access[user_id] = datetime.utcnow()
            await state.set_state(PrivateStates.in_private_section)
            
            await callback.message.edit_text(
                "🔓 <b>Личный раздел</b>\n\n"
                "Добро пожаловать в приватную зону.\n"
                "Здесь хранятся твои личные записи.\n\n"
                f"⚠️ Автовыход через {settings.PRIVATE_AUTO_LOGOUT_MINUTES} минут бездействия.",
                reply_markup=private_section_keyboard()
            )
            
            # Запускаем таймер автовыхода
            asyncio.create_task(auto_logout(user_id, callback.message, state))
            
        else:
            # PIN неверный
            user.pin_attempts += 1
            remaining = settings.MAX_PIN_ATTEMPTS - user.pin_attempts
            
            if user.pin_attempts >= settings.MAX_PIN_ATTEMPTS:
                user.pin_blocked_until = datetime.utcnow() + timedelta(minutes=settings.PIN_BLOCK_MINUTES)
                async with db.async_session() as session:
                    await session.merge(user)
                    await session.commit()
                
                await state.clear()
                await callback.message.edit_text(
                    f"⛔ Слишком много попыток!\n\n"
                    f"Доступ заблокирован на {settings.PIN_BLOCK_MINUTES} минут."
                )
            else:
                user_data["current_pin"] = ""
                async with db.async_session() as session:
                    await session.merge(user)
                    await session.commit()
                
                await callback.message.edit_text(
                    f"❌ Неверный PIN!\n\n"
                    f"Осталось попыток: {remaining}\n\n"
                    f"Введено: ____",
                    reply_markup=pin_keyboard()
                )
            
        await callback.answer()
        return
    
    if action == "back":
        # Стереть последнюю цифру
        user_data["current_pin"] = user_data.get("current_pin", "")[:-1]
    else:
        # Добавить цифру
        if len(user_data.get("current_pin", "")) < 4:
            user_data["current_pin"] = user_data.get("current_pin", "") + action
    
    current = user_data.get("current_pin", "")
    masked = "●" * len(current) + "_" * (4 - len(current))
    
    await callback.message.edit_text(
        f"🔐 Введи PIN-код:\n\n"
        f"Введено: {masked}",
        reply_markup=pin_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data.startswith("pin_"), StateFilter(PrivateStates.waiting_pin_new))
async def pin_creation_digit(callback: CallbackQuery, state: FSMContext):
    """Создание нового PIN"""
    action = callback.data.replace("pin_", "")
    user_id = callback.from_user.id
    user_data = get_user_data(user_id)
    
    if action == "confirm":
        new_pin = user_data.get("new_pin", "")
        
        if len(new_pin) != 4:
            await callback.answer("PIN должен содержать 4 цифры!")
            return
        
        # Сохраняем PIN
        user = await db.get_user(user_id)
        user.pin_code = new_pin
        
        async with db.async_session() as session:
            await session.merge(user)
            await session.commit()
        
        private_access[user_id] = datetime.utcnow()
        await state.set_state(PrivateStates.in_private_section)
        
        await callback.message.edit_text(
            "🔐 PIN создан успешно!\n\n"
            "Добро пожаловать в Личный раздел.",
            reply_markup=private_section_keyboard()
        )
        
        asyncio.create_task(auto_logout(user_id, callback.message, state))
        await callback.answer()
        return
    
    if action == "back":
        user_data["new_pin"] = user_data.get("new_pin", "")[:-1]
    else:
        if len(user_data.get("new_pin", "")) < 4:
            user_data["new_pin"] = user_data.get("new_pin", "") + action
    
    current = user_data.get("new_pin", "")
    masked = "●" * len(current) + "_" * (4 - len(current))
    
    await callback.message.edit_text(
        f"🔐 Создай PIN-код:\n\n"
        f"Введено: {masked}",
        reply_markup=pin_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data == "private_entries")
async def private_entries(callback: CallbackQuery):
    """Просмотр личных записей"""
    user = await db.get_user(callback.from_user.id)
    entries = user.private_entries
    
    if not entries:
        await callback.answer("У тебя нет записей")
        await callback.message.edit_text(
            "📝 У тебя пока нет личных записей.\n\n"
            "Создай первую запись:",
            reply_markup=private_section_keyboard()
        )
        return
    
    text = "📝 <b>Твои записи:</b>\n\n"
    for i, entry in enumerate(entries[-10:], 1):  # Последние 10 записей
        preview = entry.content[:50] + "..." if len(entry.content) > 50 else entry.content
        text += f"{i}. {preview}\n"
    
    await callback.message.edit_text(text, reply_markup=private_section_keyboard())
    await callback.answer()
@router.callback_query(F.data == "private_new")
async def private_new_entry(callback: CallbackQuery, state: FSMContext):
    """Новая запись"""
    await state.set_state(PrivateStates.waiting_entry_content)
    await callback.message.edit_text(
        "📝 <b>Новая запись</b>\n\n"
        "Напиши текст записи (только ты видишь эти записи):"
    )
    await callback.answer()
@router.message(StateFilter(PrivateStates.waiting_entry_content))
async def private_entry_content(message: Message, state: FSMContext):
    """Сохранение новой записи"""
    user = await db.get_user(message.from_user.id)
    
    async with db.async_session() as session:
        entry = db.PrivateEntry(
            user_id=user.id,
            content=message.text
        )
        session.add(entry)
        await session.commit()
    
    await state.set_state(PrivateStates.in_private_section)
    await message.answer(
        "✅ Запись сохранена!\n\n"
        "Она видна только тебе.",
        reply_markup=private_section_keyboard()
    )
@router.callback_query(F.data == "private_change_pin")
async def private_change_pin_start(callback: CallbackQuery, state: FSMContext):
    """Начало смены PIN"""
    await state.set_state(PrivateStates.waiting_pin_new)
    get_user_data(callback.from_user.id)["new_pin"] = ""
    
    await callback.message.edit_text(
        "🔐 <b>Смена PIN</b>\n\n"
        "Введи новый PIN (4 цифры):",
        reply_markup=pin_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data == "private_exit")
async def private_exit(callback: CallbackQuery, state: FSMContext):
    """Выход из приватного раздела"""
    user_id = callback.from_user.id
    
    if user_id in private_access:
        del private_access[user_id]
    
    await state.clear()
    clear_user_data(user_id)
    
    await callback.message.edit_text(
        "🔒 <b>Выход выполнен</b>\n\n"
        "Приватный раздел закрыт."
    )
    await callback.message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
    await callback.answer()

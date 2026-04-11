from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select
from db.db import async_session
from db.models import User
from keyboards.reply import main_reply_menu

router = Router()

class SettingsForm(StatesGroup):
    morning_time = State()
    evening_time = State()
    morning_text = State()
    evening_text = State()

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    tg_id = message.from_user.id
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            await message.answer("Ошибка")
            return
        text = (
            f"⚙️ <b>Настройки</b>\n\n"
            f"🌅 Утреннее сообщение: {'включено' if user.morning_enabled else 'выключено'}\n"
            f"⏰ Время: {user.morning_time}\n"
            f"📝 Текст: {user.morning_text}\n\n"
            f"🌙 Вечернее сообщение: {'включено' if user.evening_enabled else 'выключено'}\n"
            f"⏰ Время: {user.evening_time}\n"
            f"📝 Текст: {user.evening_text}\n\n"
            f"Выберите, что изменить:"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🌅 Утро (вкл/выкл)", callback_data="toggle_morning")],
            [InlineKeyboardButton(text="🌅 Утро (время)", callback_data="set_morning_time")],
            [InlineKeyboardButton(text="🌅 Утро (текст)", callback_data="set_morning_text")],
            [InlineKeyboardButton(text="🌙 Вечер (вкл/выкл)", callback_data="toggle_evening")],
            [InlineKeyboardButton(text="🌙 Вечер (время)", callback_data="set_evening_time")],
            [InlineKeyboardButton(text="🌙 Вечер (текст)", callback_data="set_evening_text")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
        ])
        await message.answer(text, reply_markup=kb)

@router.callback_query(F.data == "toggle_morning")
async def toggle_morning(callback: CallbackQuery):
    tg_id = callback.from_user.id
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.morning_enabled = not user.morning_enabled
            await session.commit()
    await callback.answer("Утренние сообщения " + ("включены" if user.morning_enabled else "выключены"))
    await settings_menu(callback.message)

@router.callback_query(F.data == "toggle_evening")
async def toggle_evening(callback: CallbackQuery):
    tg_id = callback.from_user.id
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            user.evening_enabled = not user.evening_enabled
            await session.commit()
    await callback.answer("Вечерние сообщения " + ("включены" if user.evening_enabled else "выключены"))
    await settings_menu(callback.message)

@router.callback_query(F.data == "set_morning_time")
async def set_morning_time(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новое время для утреннего сообщения в формате ЧЧ:ММ (например, 08:00):")
    await state.set_state(SettingsForm.morning_time)
    await callback.answer()

@router.message(SettingsForm.morning_time)
async def save_morning_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    if len(time_str) != 5 or time_str[2] != ':' or not time_str[:2].isdigit() or not time_str[3:].isdigit():
        await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ")
        return
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            user.morning_time = time_str
            await session.commit()
    await message.answer(f"✅ Время утреннего сообщения изменено на {time_str}")
    await state.clear()
    await settings_menu(message)

@router.callback_query(F.data == "set_evening_time")
async def set_evening_time(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новое время для вечернего сообщения в формате ЧЧ:ММ (например, 23:00):")
    await state.set_state(SettingsForm.evening_time)
    await callback.answer()

@router.message(SettingsForm.evening_time)
async def save_evening_time(message: Message, state: FSMContext):
    time_str = message.text.strip()
    if len(time_str) != 5 or time_str[2] != ':' or not time_str[:2].isdigit() or not time_str[3:].isdigit():
        await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ")
        return
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            user.evening_time = time_str
            await session.commit()
    await message.answer(f"✅ Время вечернего сообщения изменено на {time_str}")
    await state.clear()
    await settings_menu(message)

@router.callback_query(F.data == "set_morning_text")
async def set_morning_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый текст для утреннего сообщения (можно с эмодзи):")
    await state.set_state(SettingsForm.morning_text)
    await callback.answer()

@router.message(SettingsForm.morning_text)
async def save_morning_text(message: Message, state: FSMContext):
    text = message.text.strip()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            user.morning_text = text
            await session.commit()
    await message.answer(f"✅ Текст утреннего сообщения изменён.")
    await state.clear()
    await settings_menu(message)

@router.callback_query(F.data == "set_evening_text")
async def set_evening_text(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите новый текст для вечернего сообщения (можно с эмодзи):")
    await state.set_state(SettingsForm.evening_text)
    await callback.answer()

@router.message(SettingsForm.evening_text)
async def save_evening_text(message: Message, state: FSMContext):
    text = message.text.strip()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            user.evening_text = text
            await session.commit()
    await message.answer(f"✅ Текст вечернего сообщения изменён.")
    await state.clear()
    await settings_menu(message)

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    tg_id = callback.from_user.id
    is_admin = (tg_id == 8666952157)
    await callback.message.edit_text("Главное меню:")
    await callback.message.answer("Выберите действие:", reply_markup=main_reply_menu(is_admin=is_admin))
    await callback.answer()

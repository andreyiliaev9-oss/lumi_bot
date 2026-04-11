from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards.inline import admin_main_kb, admin_compliments_kb
from db.db import async_session
from db.models import User, Compliment, DiaryEntry, Base
from sqlalchemy import select, func, update

router = Router()

class AdminStates(StatesGroup):
    waiting_for_compliment = State()
    waiting_for_broadcast = State()
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()

@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID: return
    await message.answer("👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ ЛЮМИ</b>", reply_markup=admin_main_kb(), parse_mode="HTML")

@router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery):
    await callback.message.edit_text("👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ ЛЮМИ</b>", reply_markup=admin_main_kb(), parse_mode="HTML")

# --- СТАТИСТИКА ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with async_session() as session:
        u_count = await session.scalar(select(func.count(User.id)))
        d_count = await session.scalar(select(func.count(DiaryEntry.id)))
    await callback.message.edit_text(f"📊 <b>СТАТИСТИКА</b>\n\nЮзеров: {u_count}\nЗаписей: {d_count}", 
                                     reply_markup=admin_main_kb(), parse_mode="HTML")

# --- ВРЕМЯ (ТЗ 2.8) ---
@router.callback_query(F.data == "admin_time_settings")
async def time_settings(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == ADMIN_ID))
    
    text = f"⏰ <b>ВРЕМЯ</b>\n☀️ Утро: {user.morning_time if user else '19:00'}\n🌙 Вечер: {user.evening_time if user else '23:00'}"
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Утро ☀️", callback_data="set_morning_t")],
        [InlineKeyboardButton(text="Вечер 🌙", callback_data="set_evening_t")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "set_morning_t")
async def set_morning(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введи время (ЧЧ:ММ):")
    await state.set_state(AdminStates.waiting_for_morning_time)

@router.message(AdminStates.waiting_for_morning_time)
async def save_morning(message: Message, state: FSMContext):
    async with async_session() as session:
        await session.execute(update(User).values(morning_time=message.text))
        await session.commit()
    await message.answer(f"✅ Утро теперь в {message.text}", reply_markup=admin_main_kb())
    await state.clear()

# --- КОМПЛИМЕНТЫ ---
@router.callback_query(F.data == "admin_compliments")
async def admin_comp(callback: CallbackQuery):
    await callback.message.edit_text("❤️ <b>КОМПЛИМЕНТЫ</b>", reply_markup=admin_compliments_kb(), parse_mode="HTML")

@router.callback_query(F.data == "add_compliment")
async def add_comp_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напиши текст:")
    await state.set_state(AdminStates.waiting_for_compliment)

@router.message(AdminStates.waiting_for_compliment)
async def add_comp_save(message: Message, state: FSMContext):
    async with async_session() as session:
        session.add(Compliment(text=message.text))
        await session.commit()
    await message.answer("✅ Добавлено", reply_markup=admin_main_kb())
    await state.clear()

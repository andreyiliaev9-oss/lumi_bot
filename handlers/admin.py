from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards.inline import admin_main_kb, admin_compliments_kb
from db.db import async_session
from db.models import User, Compliment, DiaryEntry, Base
from sqlalchemy import select, func, update

router = Router()

# Состояния для ввода данных (FSM)
class AdminStates(StatesGroup):
    waiting_for_compliment = State()
    waiting_for_broadcast = State()
    waiting_for_cycle_tip = State()
    waiting_for_morning_text = State()

# --- ОСНОВНОЕ МЕНЮ ---
@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ ЛЮМИ</b>\n\n"
        "Здесь ты можешь управлять контентом, смотреть статистику и делать рассылки.",
        reply_markup=admin_main_kb(), 
        parse_mode="HTML"
    )

# --- БЛОК СТАТИСТИКИ (Раздел 2.7 ТЗ) ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with async_session() as session:
        users_count = await session.scalar(select(func.count(User.id)))
        diary_count = await session.scalar(select(func.count(DiaryEntry.id)))
        comp_count = await session.scalar(select(func.count(Compliment.id)))
        
    text = (
        "📊 <b>ТЕКУЩАЯ СТАТИСТИКА</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"👥 Всего девушек в базе: <b>{users_count}</b>\n"
        f"📝 Записей в дневниках: <b>{diary_count}</b>\n"
        f"❤️ База комплиментов: <b>{comp_count}</b>\n"
        "━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, reply_markup=admin_main_kb(), parse_mode="HTML")

# --- УПРАВЛЕНИЕ КОМПЛИМЕНТАМИ (Раздел 2.4 ТЗ) ---
@router.callback_query(F.data == "admin_compliments")
async def manage_compliments(callback: CallbackQuery):
    await callback.message.edit_text(
        "❤️ <b>УПРАВЛЕНИЕ КОМПЛИМЕНТАМИ</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_compliments_kb(),
        parse_mode="HTML"
    )

@router.callback_query(F.data == "add_compliment")
async def start_add_comp(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Напиши текст нового комплимента:")
    await state.set_state(AdminStates.waiting_for_compliment)

@router.message(AdminStates.waiting_for_compliment)
async def save_compliment(message: Message, state: FSMContext):
    async with async_session() as session:
        new_comp = Compliment(text=message.text, is_active=True)
        session.add(new_comp)
        await session.commit()
    await message.answer(f"✅ Добавлено: {message.text}", reply_markup=admin_main_kb())
    await state.clear()

# --- РАССЫЛКА (Раздел 2.7 ТЗ) ---
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст сообщения для <b>ВСЕХ</b> пользователей:", parse_mode="HTML")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def run_broadcast(message: Message, state: FSMContext, bot):
    async with async_session() as session:
        users = await session.scalars(select(User.tg_id))
        
    count = 0
    for user_id in users:
        try:
            await bot.send_message(user_id, message.text)
            count += 1
        except Exception:
            continue
            
    await message.answer(f"📢 Рассылка завершена!\nПолучили: {count} пользователей.")
    await state.clear()

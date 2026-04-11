from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_ID
from keyboards.inline import admin_main_kb, admin_compliments_kb
from db.db import async_session
from db.models import User, Compliment, DiaryEntry
from sqlalchemy import select, func, update

router = Router()

# Состояния для ввода данных
class AdminStates(StatesGroup):
    waiting_for_compliment = State()
    waiting_for_broadcast = State()
    waiting_for_morning_time = State()
    waiting_for_evening_time = State()

# --- ВХОД В АДМИНКУ ---
@router.message(F.text == "⚙️ Админ-панель")
async def admin_panel(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    await message.answer(
        "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ ЛЮМИ</b>\n\n"
        "Здесь вы можете управлять контентом и следить за статистикой.",
        reply_markup=admin_main_kb(), 
        parse_mode="HTML"
    )

@router.callback_query(F.data == "admin_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id != ADMIN_ID: return
    await state.clear()
    await callback.message.edit_text(
        "👑 <b>ПАНЕЛЬ УПРАВЛЕНИЯ ЛЮМИ</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML"
    )

# --- БЛОК СТАТИСТИКИ ---
@router.callback_query(F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with async_session() as session:
        u_count = await session.scalar(select(func.count(User.id)))
        d_count = await session.scalar(select(func.count(DiaryEntry.id)))
        c_count = await session.scalar(select(func.count(Compliment.id)))
        
    text = (
        "📊 <b>АКТУАЛЬНАЯ СТАТИСТИКА</b>\n"
        "━━━━━━━━━━━━━━━\n"
        f"👤 Пользователей: <b>{u_count}</b>\n"
        f"📝 Записей в дневниках: <b>{d_count}</b>\n"
        f"❤️ База комплиментов: <b>{c_count}</b>\n"
        "━━━━━━━━━━━━━━━"
    )
    await callback.message.edit_text(text, reply_markup=admin_main_kb(), parse_mode="HTML")

# --- УПРАВЛЕНИЕ ВРЕМЕНЕМ (ТЗ 2.8) ---
@router.callback_query(F.data == "admin_time_settings")
async def admin_time_menu(callback: CallbackQuery):
    async with async_session() as session:
        # Берем настройки админа как образец
        user = await session.scalar(select(User).where(User.tg_id == ADMIN_ID))
    
    text = (
        "⏰ <b>НАСТРОЙКИ УВЕДОМЛЕНИЙ</b>\n\n"
        f"☀️ Утро (рассылка): <b>{user.morning_time}</b>\n"
        f"🌙 Вечер (отчет): <b>{user.evening_time}</b>\n\n"
        "<i>Изменение применится для всех пользователей!</i>"
    )
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Изменить Утро ☀️", callback_data="set_morning_t")],
        [InlineKeyboardButton(text="Изменить Вечер 🌙", callback_data="set_evening_t")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_main")]
    ])
    await callback.message.edit_text(text, reply_markup=kb, parse_mode="HTML")

@router.callback_query(F.data == "set_morning_t")
async def set_morning_step(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите время утра в формате ЧЧ:ММ (например, 08:30):")
    await state.set_state(AdminStates.waiting_for_morning_time)

@router.message(AdminStates.waiting_for_morning_time)
async def save_morning_time(message: Message, state: FSMContext):
    new_time = message.text.strip()
    async with async_session() as session:
        await session.execute(update(User).values(morning_time=new_time))
        await session.commit()
    await message.answer(f"✅ Время утренней рассылки изменено на {new_time}", reply_markup=admin_main_kb())
    await state.clear()

# --- РАССЫЛКА ---
@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст сообщения для массовой рассылки:")
    await state.set_state(AdminStates.waiting_for_broadcast)

@router.message(AdminStates.waiting_for_broadcast)
async def run_broadcast(message: Message, state: FSMContext, bot: Bot):
    async with async_session() as session:
        users = await session.scalars(select(User.tg_id))
    
    count = 0
    for uid in users:
        try:
            await bot.send_message(uid, message.text)
            count += 1
        except Exception: continue
    
    await message.answer(f"📢 Рассылка завершена!\nУспешно отправлено: <b>{count}</b>", parse_mode="HTML", reply_markup=admin_main_kb())
    await state.clear()

# --- КОМПЛИМЕНТЫ ---
@router.callback_query(F.data == "admin_compliments")
async def manage_compliments(callback: CallbackQuery):
    await callback.message.edit_text("❤️ <b>БАЗА КОМПЛИМЕНТОВ</b>", reply_markup=admin_compliments_kb(), parse_mode="HTML")

@router.callback_query(F.data == "add_compliment")
async def add_comp_step(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите текст нового комплимента:")
    await state.set_state(AdminStates.waiting_for_compliment)

@router.message(AdminStates.waiting_for_compliment)
async def save_compliment(message: Message, state: FSMContext):
    async with async_session() as session:
        session.add(Compliment(text=message.text))
        await session.commit()
    await message.answer("✅ Комплимент успешно добавлен!", reply_markup=admin_main_kb())
    await state.clear()

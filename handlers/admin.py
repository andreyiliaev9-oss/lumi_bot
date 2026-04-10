from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import date, datetime
from sqlalchemy import select, func
from config import ADMIN_ID
from db.db import async_session
from db.models import User, CycleTip, Habit, Event, DiaryEntry

router = Router()

# Состояния для FSM
class TipForm(StatesGroup):
    phase = State()
    tip_text = State()

class BroadcastForm(StatesGroup):
    text = State()
    confirm = State()

# ---------- Вспомогательные функции ----------
async def is_admin(user_id: int) -> bool:
    return user_id == ADMIN_ID

def get_phase_emoji(phase: str) -> str:
    return {"menstruation":"🩸", "follicular":"🌱", "ovulation":"🥚", "luteal":"🌙"}.get(phase, "📌")

# ---------- Главное меню админа ----------
@router.message(F.from_user.id == ADMIN_ID, F.text == "/admin")
async def admin_panel(message: Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🌸 Советы по циклу", callback_data="admin_tips")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
    ])
    await message.answer("👑 Админ-панель", reply_markup=kb)

# ---------- Управление советами ----------
@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "admin_tips")
async def manage_tips(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить совет", callback_data="add_tip")],
        [InlineKeyboardButton(text="📋 Список советов", callback_data="list_tips")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])
    await callback.message.edit_text("Управление советами по фазам цикла:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "add_tip")
async def add_tip_phase(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🩸 Месячные", callback_data="phase_menstruation")],
        [InlineKeyboardButton(text="🌱 Фолликулярная", callback_data="phase_follicular")],
        [InlineKeyboardButton(text="🥚 Овуляция", callback_data="phase_ovulation")],
        [InlineKeyboardButton(text="🌙 Лютеиновая", callback_data="phase_luteal")]
    ])
    await callback.message.edit_text("Выберите фазу цикла для совета:", reply_markup=kb)
    await state.set_state(TipForm.phase)
    await callback.answer()

@router.callback_query(F.from_user.id == ADMIN_ID, TipForm.phase)
async def add_tip_text(callback: CallbackQuery, state: FSMContext):
    phase = callback.data.split("_")[1]  # 'menstruation', 'follicular'...
    await state.update_data(phase=phase)
    await callback.message.edit_text("Введите текст совета (можно с эмодзи и переносами):")
    await state.set_state(TipForm.tip_text)
    await callback.answer()

@router.message(F.from_user.id == ADMIN_ID, TipForm.tip_text)
async def save_tip(message: Message, state: FSMContext):
    tip_text = message.text
    data = await state.get_data()
    async with async_session() as session:
        tip = CycleTip(phase=data['phase'], tip=tip_text)
        session.add(tip)
        await session.commit()
    await message.answer("✅ Совет добавлен!", reply_markup=await back_to_admin_kb())
    await state.clear()

@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "list_tips")
async def list_tips(callback: CallbackQuery):
    async with async_session() as session:
        tips = await session.execute(select(CycleTip).order_by(CycleTip.phase))
        tips_list = tips.scalars().all()
        if not tips_list:
            text = "Советов пока нет. Добавьте первый."
            await callback.message.edit_text(text, reply_markup=await back_to_admin_kb())
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            for tip in tips_list:
                emoji = get_phase_emoji(tip.phase)
                btn_text = f"{emoji} {tip.phase.capitalize()} (ID {tip.id})"
                kb.inline_keyboard.append([InlineKeyboardButton(text=btn_text, callback_data=f"tip_{tip.id}")])
            kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_tips")])
            await callback.message.edit_text("Выберите совет для удаления:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.from_user.id == ADMIN_ID, F.data.startswith("tip_"))
async def delete_tip(callback: CallbackQuery):
    tip_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        tip = await session.get(CycleTip, tip_id)
        if tip:
            await session.delete(tip)
            await session.commit()
            await callback.answer("Совет удалён")
            await list_tips(callback)
        else:
            await callback.answer("Не найден")

# ---------- Рассылка ----------
@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "admin_broadcast")
async def broadcast_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите текст рассылки (можно с HTML-разметкой):")
    await state.set_state(BroadcastForm.text)
    await callback.answer()

@router.message(F.from_user.id == ADMIN_ID, BroadcastForm.text)
async def broadcast_text(message: Message, state: FSMContext):
    text = message.html_text
    await state.update_data(text=text)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Отправить", callback_data="broadcast_confirm"),
         InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_admin")]
    ])
    await message.answer(f"Подтвердите рассылку:\n\n{text}", reply_markup=kb)
    await state.set_state(BroadcastForm.confirm)

@router.callback_query(F.from_user.id == ADMIN_ID, BroadcastForm.confirm, F.data == "broadcast_confirm")
async def broadcast_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    text = data.get('text')
    async with async_session() as session:
        users = await session.execute(select(User).where(User.is_active == True))
        users_list = users.scalars().all()
        success = 0
        for user in users_list:
            try:
                await callback.bot.send_message(user.tg_id, text)
                success += 1
            except:
                pass
    await callback.message.edit_text(f"📢 Рассылка завершена. Отправлено {success} из {len(users_list)} пользователям.")
    await state.clear()
    await callback.answer()

@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "back_to_admin")
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await admin_panel(callback.message)
    await callback.answer()

# ---------- Статистика ----------
@router.callback_query(F.from_user.id == ADMIN_ID, F.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):
    async with async_session() as session:
        total_users = await session.scalar(select(func.count(User.id)))
        active_today = await session.scalar(select(func.count(User.id)).where(User.reg_date >= date.today()))
        total_habits = await session.scalar(select(func.count(Habit.id)))
        total_events = await session.scalar(select(func.count(Event.id)))
        total_diary = await session.scalar(select(func.count(DiaryEntry.id)))
        total_tips = await session.scalar(select(func.count(CycleTip.id)))
        
        text = (f"📊 <b>Статистика бота</b>\n\n"
                f"👥 Всего пользователей: {total_users}\n"
                f"🆕 Зарегистрировались сегодня: {active_today}\n"
                f"✅ Привычек создано: {total_habits}\n"
                f"📅 Событий создано: {total_events}\n"
                f"📔 Записей в дневнике: {total_diary}\n"
                f"🌸 Советов по циклу: {total_tips}")
        await callback.message.edit_text(text, reply_markup=await back_to_admin_kb())
    await callback.answer()

# Вспомогательная клавиатура "Назад"
async def back_to_admin_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_admin")]
    ])

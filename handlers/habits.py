from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime
from sqlalchemy import select
from db.db import async_session
from db.models import Habit
from keyboards.inline import back_button

router = Router()

class HabitForm(StatesGroup):
    name = State()
    description = State()
    time = State()
    frequency = State()

@router.callback_query(F.data == "habits")
async def habits_menu(callback: CallbackQuery):
    await callback.message.edit_text("Управление привычками:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить привычку", callback_data="add_habit")],
        [InlineKeyboardButton(text="📋 Мои привычки", callback_data="list_habits")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="start")]
    ]))
    await callback.answer()

@router.callback_query(F.data == "add_habit")
async def add_habit_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название привычки:")
    await state.set_state(HabitForm.name)
    await callback.answer()

@router.message(HabitForm.name)
async def get_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Введите описание (или '-' для пропуска)")
    await state.set_state(HabitForm.description)

@router.message(HabitForm.description)
async def get_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else ""
    await state.update_data(description=desc)
    await message.answer("Введите время в формате ЧЧ:ММ (например, 09:00)")
    await state.set_state(HabitForm.time)

@router.message(HabitForm.time)
async def get_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
    except:
        await message.answer("Неверный формат. Используйте ЧЧ:ММ")
        return
    await state.update_data(time=message.text)
    await message.answer("Частота: 'ежедневно' или номера дней через пробел (1=пн, 7=вс)")
    await state.set_state(HabitForm.frequency)

@router.message(HabitForm.frequency)
async def get_freq(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        habit = Habit(
            user_id=message.from_user.id,
            name=data['name'],
            description=data['description'],
            time=data['time'],
            frequency=message.text
        )
        session.add(habit)
        await session.commit()
    await message.answer("✅ Привычка добавлена!", reply_markup=back_button("habits"))
    await state.clear()

@router.callback_query(F.data == "list_habits")
async def list_habits(callback: CallbackQuery):
    async with async_session() as session:
        habits = await session.execute(select(Habit).where(Habit.user_id == callback.from_user.id))
        habits_list = habits.scalars().all()
        if not habits_list:
            text = "📭 У вас пока нет привычек. Добавьте первую через меню."
        else:
            text = "📋 Ваши привычки:\n\n" + "\n".join([f"• {h.name} — в {h.time}" for h in habits_list])
        await callback.message.edit_text(text, reply_markup=back_button("habits"))
    await callback.answer()

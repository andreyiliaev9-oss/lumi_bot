from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date
from sqlalchemy import select
from db.db import async_session
from db.models import User, Habit, HabitLog
from keyboards.inline import back_button, habit_frequency_keyboard
from keyboards.reply import main_reply_menu

router = Router()

class HabitForm(StatesGroup):
    name = State()
    description = State()
    time = State()
    frequency = State()
    month_days = State()

@router.callback_query(F.data == "habits")
async def habits_menu(callback: CallbackQuery):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить привычку", callback_data="add_habit")],
        [InlineKeyboardButton(text="📋 Мои привычки", callback_data="list_habits")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
    ])
    await callback.message.edit_text("Управление привычками:", reply_markup=kb)
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
    await message.answer("Введите время в формате <b>ЧЧ:ММ</b> (например, 09:00):")
    await state.set_state(HabitForm.time)

@router.message(HabitForm.time)
async def get_time(message: Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
    except:
        await message.answer("❌ Неверный формат. Используйте ЧЧ:ММ")
        return
    await state.update_data(time=message.text)
    await message.answer("Выберите частоту:", reply_markup=habit_frequency_keyboard())
    await state.set_state(HabitForm.frequency)

@router.callback_query(HabitForm.frequency, F.data.startswith("freq_"))
async def get_frequency(callback: CallbackQuery, state: FSMContext):
    choice = callback.data
    if choice == "freq_month_days":
        await callback.message.edit_text("Введите числа месяца через запятую (например, 1,15):")
        await state.set_state(HabitForm.month_days)
        await callback.answer()
        return
    elif choice == "freq_custom":
        await callback.message.edit_text("Введите номера дней недели через пробел (1=пн, 7=вс):")
        await state.set_state(HabitForm.month_days)
        await callback.answer()
        return
    freq_map = {
        "freq_everyday": "everyday",
        "freq_135": "1,3,5",
        "freq_24": "2,4",
        "freq_67": "6,7"
    }
    frequency = freq_map.get(choice, "everyday")
    await save_habit(callback.from_user.id, await state.get_data(), frequency, callback.message)
    await state.clear()

@router.message(HabitForm.month_days)
async def get_custom_days(message: Message, state: FSMContext):
    text = message.text.strip()
    if text.replace(",", " ").replace(" ", "").isdigit():
        frequency = f"month_days:{text}"
    else:
        parts = text.split()
        if all(p.isdigit() and 1 <= int(p) <= 7 for p in parts):
            frequency = ",".join(parts)
        else:
            await message.answer("❌ Неверный формат. Введите числа месяца через запятую или дни недели через пробел.")
            return
    data = await state.get_data()
    await save_habit(message.from_user.id, data, frequency, message)
    await state.clear()

async def save_habit(user_tg_id, data, frequency, message_obj):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == user_tg_id))
        if not user:
            await message_obj.answer("Ошибка: пользователь не найден")
            return
        habit = Habit(
            user_id=user.id,
            name=data['name'],
            description=data['description'],
            time=data['time'],
            frequency=frequency
        )
        session.add(habit)
        await session.commit()
    await message_obj.answer("✅ Привычка добавлена!", reply_markup=main_reply_menu(user_tg_id == 8666952157))

@router.callback_query(F.data == "list_habits")
async def list_habits(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        if not user:
            await callback.answer("Ошибка")
            return
        habits = await session.execute(select(Habit).where(Habit.user_id == user.id, Habit.is_active == True))
        habits_list = habits.scalars().all()
        if not habits_list:
            text = "📭 У вас нет привычек. Добавьте первую через меню."
        else:
            text = "📋 Ваши привычки:\n\n"
            for h in habits_list:
                text += f"• <b>{h.name}</b> в {h.time}\n"
                text += f"  {h.description or ''}\n"
                text += f"  Частота: {h.frequency}\n"
                text += f"  Команды: /done_{h.id} | /skip_{h.id}\n\n"
        await callback.message.edit_text(text, reply_markup=back_button("habits"))
    await callback.answer()

@router.message(lambda m: m.text and m.text.startswith("/done_"))
async def complete_habit(message: Message):
    habit_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        habit = await session.get(Habit, habit_id)
        if not habit or habit.user_id != user.id:
            await message.answer("Привычка не найдена")
            return
        today = date.today()
        existing = await session.scalar(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.date == today))
        if existing:
            await message.answer("Вы уже отмечали эту привычку сегодня.")
            return
        log = HabitLog(habit_id=habit_id, user_id=user.id, completed=True)
        session.add(log)
        await session.commit()
    await message.answer("✅ Отлично! Привычка выполнена.")

@router.message(lambda m: m.text and m.text.startswith("/skip_"))
async def skip_habit(message: Message):
    habit_id = int(message.text.split("_")[1])
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        habit = await session.get(Habit, habit_id)
        if not habit or habit.user_id != user.id:
            await message.answer("Привычка не найдена")
            return
        today = date.today()
        existing = await session.scalar(select(HabitLog).where(HabitLog.habit_id == habit_id, HabitLog.date == today))
        if existing:
            await message.answer("Вы уже отмечали эту привычку сегодня.")
            return
        log = HabitLog(habit_id=habit_id, user_id=user.id, skipped=True)
        session.add(log)
        await session.commit()
    await message.answer("⏭ Пропущено. В следующий раз получится!")

import asyncio
import logging
from datetime import datetime
import aiosqlite
import pytz

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.database import init_db, DB_NAME

# --- КОНФИГ ---
API_TOKEN = '8690428738:AAGUuo-V3id99Z-3UsT6twy2bJGmScCXFbA'
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

# --- СОСТОЯНИЯ ---
class RegisterStates(StatesGroup):
    waiting_for_name = State()
    waiting_for_gender = State()

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()

class HabitStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()

# --- КЛАВИАТУРЫ ---
def main_menu():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🗓 Планировщик")],
        [KeyboardButton(text="🌸 Комплимент"), KeyboardButton(text="🆘 Поддержка")],
        [KeyboardButton(text="🔄 Привычки"), KeyboardButton(text="🔒 Приватное")]
    ], resize_keyboard=True)

def gender_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Мужской 👨", callback_data="gender_m"),
         InlineKeyboardButton(text="Женский 👩", callback_data="gender_f")]
    ])

# --- РЕГИСТРАЦИЯ С ПОЛОМ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_registered FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            user = await cursor.fetchone()
        
        if not user or user[0] == 0:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, is_registered) VALUES (?, ?, 0)", 
                             (message.from_user.id, message.from_user.username))
            await db.commit()
            await message.answer("✨ Добро пожаловать в ЛЮМИ. Как мне к тебе обращаться?")
            await state.set_state(RegisterStates.waiting_for_name)
        else:
            await message.answer("Система активна.", reply_markup=main_menu())

@dp.message(RegisterStates.waiting_for_name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(f"Приятно познакомиться, {message.text}! Теперь укажи свой пол:", reply_markup=gender_kb())
    await state.set_state(RegisterStates.waiting_for_gender)

@dp.callback_query(RegisterStates.waiting_for_gender)
async def reg_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = "m" if callback.data == "gender_m" else "f"
    data = await state.get_data()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET first_name = ?, gender = ?, is_registered = 1 WHERE user_id = ?", 
                         (data['name'], gender, callback.from_user.id))
        await db.commit()
    await callback.message.delete()
    await callback.message.answer(f"Всё готово, {data['name']}! Теперь ты в системе.", reply_markup=main_menu())
    await state.clear()

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date, gender FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
    if row:
        name, streak, joined, gender = row
        g_label = "Мужчина" if gender == "m" else "Женщина"
        text = f"👤 ПРОФИЛЬ: {name}\nПол: {g_label}\nСерия: {streak} дн.\nС нами с: {joined[:10]}"
        await message.answer(text)

# --- ПЛАНИРОВЩИК (СТАРЫЙ) ---
@dp.message(F.text == "🗓 Планировщик")
async def plan_start(message: types.Message, state: FSMContext):
    await message.answer("📝 Название задачи:")
    await state.set_state(TaskStates.waiting_for_title)

@dp.message(TaskStates.waiting_for_title)
async def plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📅 Время (ДД.ММ ЧЧ:ММ):")
    await state.set_state(TaskStates.waiting_for_time)

@dp.message(TaskStates.waiting_for_time)
async def plan_time(message: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(f"{message.text}.{datetime.now().year}", "%d.%m %H:%M.%Y")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO tasks (user_id, title, task_time) VALUES (?, ?, ?)",
                             (message.from_user.id, data['title'], dt.strftime("%Y-%m-%d %H:%M:00")))
            await db.commit()
        await message.answer(f"✅ Задача создана!")
        await state.clear()
    except: await message.answer("Ошибка формата!")

# --- ПРИВЫЧКИ (НОВОЕ) ---
@dp.message(F.text == "🔄 Привычки")
async def habit_menu(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (message.from_user.id,)) as cursor:
            count = (await cursor.fetchone())[0]
    
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="➕ Добавить (До 5)", callback_data="add_habit")]])
    await message.answer(f"Твои привычки (Активно: {count}/5).", reply_markup=kb)

@dp.callback_query(F.data == "add_habit")
async def add_habit_start(callback: types.CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (callback.from_user.id,)) as cursor:
            if (await cursor.fetchone())[0] >= 5:
                return await callback.answer("Лимит 5 привычек!", show_alert=True)
    await callback.message.answer("📝 Название привычки:")
    await state.set_state(HabitStates.waiting_for_title)

@dp.message(HabitStates.waiting_for_title)
async def habit_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("⏰ Время напоминания (ЧЧ:ММ):")
    await state.set_state(HabitStates.waiting_for_time)

@dp.message(HabitStates.waiting_for_time)
async def habit_time(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO habits (user_id, title, remind_time) VALUES (?, ?, ?)",
                             (message.from_user.id, data['title'], message.text))
            await db.commit()
        await message.answer(f"✅ Привычка «{data['title']}» добавлена!")
        await state.clear()
    except: await message.answer("Формат: ЧЧ:ММ")

# --- ФОНОВЫЕ ПРОВЕРКИ ---
async def check_everything():
    now_full = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    now_time = datetime.now(MOSCOW_TZ).strftime("%H:%M")
    
    async with aiosqlite.connect(DB_NAME) as db:
        # 1. Разовые задачи
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now_full,)) as cursor:
            for tid, uid, title in await cursor.fetchall():
                try:
                    await bot.send_message(uid, f"🔔 ЗАДАЧА: {title}")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                except: pass
        
        # 2. Дневные напоминания о привычках
        async with db.execute("SELECT user_id, title FROM habits WHERE remind_time = ?", (now_time,)) as cursor:
            for uid, title in await cursor.fetchall():
                try: await bot.send_message(uid, f"💡 Пора сделать: {title}")
                except: pass
        
        # 3. Вечерний опрос (19:00)
        if now_time == "19:00":
            async with db.execute("SELECT h.habit_id, h.user_id, h.title, u.gender, u.first_name FROM habits h JOIN users u ON h.user_id = u.user_id") as cursor:
                for hid, uid, title, gender, name in await cursor.fetchall():
                    word = "сделал" if gender == "m" else "сделала"
                    kb = InlineKeyboardMarkup(inline_keyboard=[[
                        InlineKeyboardButton(text="✅ Да", callback_data=f"h_done_{hid}"),
                        InlineKeyboardButton(text="❌ Нет", callback_data=f"h_no")
                    ]])
                    try: await bot.send_message(uid, f"❓ {name}, ты сегодня {word} привычку: {title}?", reply_markup=kb)
                    except: pass
        await db.commit()

@dp.callback_query(F.data.startswith("h_done_"))
async def habit_done(callback: types.CallbackQuery):
    hid = callback.data.split("_")[2]
    today = datetime.now(MOSCOW_TZ).date().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE habits SET streak = streak + 1, last_completed = ? WHERE habit_id = ?", (today, hid))
        await db.commit()
    await callback.message.edit_text("🔥 Красава! Серия продлена.")

@dp.callback_query(F.data == "h_no")
async def habit_not_done(callback: types.CallbackQuery):
    await callback.message.edit_text("Нужно дожать! Еще есть время до конца дня.")

async def main():
    await init_db()
    scheduler.add_job(check_everything, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

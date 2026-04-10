import asyncio
import logging
from datetime import datetime, date
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

# --- РЕГИСТРАЦИЯ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT is_registered FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            user = await cursor.fetchone()
        if not user or user[0] == 0:
            await db.execute("INSERT OR IGNORE INTO users (user_id, username, is_registered) VALUES (?, ?, 0)", (message.from_user.id, message.from_user.username))
            await db.commit()
            await message.answer("✨ Система ЛЮМИ активирована. Как мне к тебе обращаться?")
            await state.set_state(RegisterStates.waiting_for_name)
        else:
            await message.answer("С возвращением!", reply_markup=main_menu())

@dp.message(RegisterStates.waiting_for_name)
async def reg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="Мужской 👨", callback_data="gender_m"), InlineKeyboardButton(text="Женский 👩", callback_data="gender_f")]])
    await message.answer(f"Приятно познакомиться, {message.text}! Укажи свой пол:", reply_markup=kb)
    await state.set_state(RegisterStates.waiting_for_gender)

@dp.callback_query(RegisterStates.waiting_for_gender)
async def reg_gender(callback: types.CallbackQuery, state: FSMContext):
    gender = "m" if callback.data == "gender_m" else "f"
    data = await state.get_data()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET first_name = ?, gender = ?, is_registered = 1 WHERE user_id = ?", (data['name'], gender, callback.from_user.id))
        await db.commit()
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(f"Регистрация завершена, {data['name']}!", reply_markup=main_menu())
    await state.clear()

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date, gender FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
    if row:
        name, streak, joined, gender = row
        g_text = "Мужчина" if gender == "m" else "Женщина"
        await message.answer(f"👤 ПРОФИЛЬ: {name}\nПол: {g_text}\nСерия: {streak} дн.\nС нами с: {joined[:10]}")

# --- ПРИВЫЧКИ ---
@dp.message(F.text == "🔄 Привычки")
async def habit_menu(message: types.Message):
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT habit_id, title, last_completed FROM habits WHERE user_id = ?", (message.from_user.id,)) as cursor:
            habits = await cursor.fetchall()
    
    kb_list = []
    for hid, title, l_comp in habits:
        status = "✅" if l_comp == today else "🔘"
        kb_list.append([InlineKeyboardButton(text=f"{status} {title}", callback_data=f"h_check_{hid}"),
                        InlineKeyboardButton(text="🗑", callback_data=f"h_del_{hid}")])
    
    kb_list.append([InlineKeyboardButton(text="➕ Добавить привычку", callback_data="add_h")])
    await message.answer("🔄 **ТВОИ ПРИВЫЧКИ**\nНажми на привычку, чтобы отметить её выполнение:", 
                         reply_markup=InlineKeyboardMarkup(inline_keyboard=kb_list), parse_mode="Markdown")

@dp.callback_query(F.data.startswith("h_check_"))
async def h_check(callback: types.CallbackQuery):
    hid = callback.data.split("_")[2]
    today = date.today().isoformat()
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE habits SET streak = streak + 1, last_completed = ? WHERE habit_id = ?", (today, hid))
        await db.commit()
    await callback.answer("Принято! Молодцом 🔥")
    await habit_menu(callback.message) # Обновляем меню
    await callback.message.delete()

@dp.callback_query(F.data.startswith("h_del_"))
async def h_del(callback: types.CallbackQuery):
    hid = callback.data.split("_")[2]
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("DELETE FROM habits WHERE habit_id = ?", (hid,))
        await db.commit()
    await callback.answer("Удалено")
    await habit_menu(callback.message)
    await callback.message.delete()

@dp.callback_query(F.data == "add_h")
async def add_h(callback: types.CallbackQuery, state: FSMContext):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT COUNT(*) FROM habits WHERE user_id = ?", (callback.from_user.id,)) as cursor:
            if (await cursor.fetchone())[0] >= 5:
                return await callback.answer("Лимит 5 привычек!", show_alert=True)
    await callback.answer()
    await callback.message.answer("Напиши название привычки:")
    await state.set_state(HabitStates.waiting_for_title)

@dp.message(HabitStates.waiting_for_title)
async def h_t_rec(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Время напоминания (ЧЧ:ММ):")
    await state.set_state(HabitStates.waiting_for_time)

@dp.message(HabitStates.waiting_for_time)
async def h_tm_rec(message: types.Message, state: FSMContext):
    try:
        datetime.strptime(message.text, "%H:%M")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO habits (user_id, title, remind_time) VALUES (?, ?, ?)", (message.from_user.id, data['title'], message.text))
            await db.commit()
        await message.answer("✅ Добавлено!")
        await state.clear()
    except: await message.answer("Формат: ЧЧ:ММ")

# --- ПЛАНИРОВЩИК ---
@dp.message(F.text == "🗓 Планировщик")
async def plan_start(message: types.Message, state: FSMContext):
    await message.answer("Название задачи:")
    await state.set_state(TaskStates.waiting_for_title)

@dp.message(TaskStates.waiting_for_title)
async def plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Время (ДД.ММ ЧЧ:ММ):")
    await state.set_state(TaskStates.waiting_for_time)

@dp.message(TaskStates.waiting_for_time)
async def plan_time(message: types.Message, state: FSMContext):
    try:
        dt = datetime.strptime(f"{message.text}.{datetime.now().year}", "%d.%m %H:%M.%Y")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO tasks (user_id, title, task_time) VALUES (?, ?, ?)", (message.from_user.id, data['title'], dt.strftime("%Y-%m-%d %H:%M:00")))
            await db.commit()
        await message.answer("✅ Готово!")
        await state.clear()
    except: await message.answer("Ошибка формата!")

# --- ФОН ---
async def worker():
    now_f = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    now_t = datetime.now(MOSCOW_TZ).strftime("%H:%M")
    today = date.today().isoformat()
    
    async with aiosqlite.connect(DB_NAME) as db:
        # Задачи
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now_f,)) as cursor:
            for tid, uid, title in await cursor.fetchall():
                try:
                    await bot.send_message(uid, f"🔔 ЗАДАЧА: {title}")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                except: pass
        # Напоминания
        async with db.execute("SELECT user_id, title FROM habits WHERE remind_time = ? AND last_completed != ?", (now_t, today)) as cursor:
            for uid, title in await cursor.fetchall():
                try: await bot.send_message(uid, f"💡 Напоминание: {title}")
                except: pass
        # Опрос 19:00
        if now_t == "19:00":
            async with db.execute("SELECT h.habit_id, h.user_id, h.title, u.gender, u.first_name FROM habits h JOIN users u ON h.user_id = u.user_id WHERE h.last_completed != ?", (today,)) as cursor:
                for hid, uid, title, gen, name in await cursor.fetchall():
                    word = "сделал" if gen == "m" else "сделала"
                    kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Да", callback_data=f"h_check_{hid}"), InlineKeyboardButton(text="❌ Нет", callback_data="h_no")]])
                    try: await bot.send_message(uid, f"❓ {name}, ты уже {word} привычку: {title}?", reply_markup=kb)
                    except: pass
        await db.commit()

async def main():
    await init_db()
    scheduler.add_job(worker, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

@dp.callback_query(F.data == "h_no")
async def h_no(c: types.CallbackQuery):
    await c.answer("Надо поднажать! 🔥")
    await c.message.edit_text("Еще есть время до конца дня. Сделай это!")

if __name__ == "__main__":
    asyncio.run(main())

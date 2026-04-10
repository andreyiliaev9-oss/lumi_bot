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

class RegisterStates(StatesGroup):
    waiting_for_name = State()

class TaskStates(StatesGroup):
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
        
        if not user:
            await db.execute("INSERT INTO users (user_id, username, is_registered) VALUES (?, ?, 0)", 
                             (message.from_user.id, message.from_user.username))
            await db.commit()
            await message.answer("✨ Добро пожаловать в ЛЮМИ. Как мне к тебе обращаться?")
            await state.set_state(RegisterStates.waiting_for_name)
        elif user[0] == 0:
            await message.answer("Как мне к тебе обращаться?")
            await state.set_state(RegisterStates.waiting_for_name)
        else:
            await message.answer("Система ЛЮМИ активна. Твой путь к гармонии продолжается.", reply_markup=main_menu())

@dp.message(RegisterStates.waiting_for_name)
async def register_name(message: types.Message, state: FSMContext):
    name = message.text
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET first_name = ?, is_registered = 1 WHERE user_id = ?", 
                         (name, message.from_user.id))
        await db.commit()
    await message.answer(f"Приятно познакомиться, {name}! Теперь всё готово к работе.", reply_markup=main_menu())
    await state.clear()

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
    
    if row:
        name, streak, joined = row
        text = (
            f"👤 ПРОФИЛЬ: {name}\n"
            f"────────────────────\n"
            f"🎖 Ранг: Исследователь\n"
            f"🔥 Серия: {streak} дн.\n"
            f"📅 С нами с: {joined[:10]}\n"
            f"────────────────────"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Достижения", callback_data="dev"), InlineKeyboardButton(text="📊 Статистика", callback_data="dev")]
        ])
        try:
            photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
            if photos.total_count > 0:
                await message.answer_photo(photos.photos[0][-1].file_id, caption=text, reply_markup=kb)
            else:
                await message.answer(text, reply_markup=kb)
        except:
            await message.answer(text, reply_markup=kb)

# --- ПЛАНИРОВЩИК ---
@dp.message(F.text == "🗓 Планировщик")
async def plan_start(message: types.Message, state: FSMContext):
    await message.answer("📝 Какое дело запланируем? (Напиши название)")
    await state.set_state(TaskStates.waiting_for_title)

@dp.message(TaskStates.waiting_for_title)
async def plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📅 На какой день и время? (Напиши в формате: 10.04 18:00)")
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
        await message.answer(f"✅ Записано: «{data['title']}» на {message.text}")
        await state.clear()
    except:
        await message.answer("❌ Неверный формат. Попробуй еще раз (например, 12.04 15:30):")

# --- ЗАГЛУШКИ ДЛЯ ОСТАЛЬНЫХ КНОПОК ---
@dp.message(F.text.in_({"🌸 Комплимент", "🆘 Поддержка", "🔄 Привычки", "🔒 Приватное"}))
async def development_msg(message: types.Message):
    await message.answer("🛠 Этот раздел сейчас находится в разработке.")

@dp.callback_query(F.data == "dev")
async def dev_callback(callback: types.CallbackQuery):
    await callback.answer("Скоро здесь что-то будет! 🛠", show_alert=True)

# --- ПРОВЕРКА ЗАДАЧ ---
async def check_tasks():
    now = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now,)) as cursor:
            tasks = await cursor.fetchall()
            for tid, uid, title in tasks:
                try:
                    await bot.send_message(uid, f"🔔 НАПОМИНАНИЕ: {title}")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                except: pass
        await db.commit()

async def main():
    await init_db()
    scheduler.add_job(check_tasks, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

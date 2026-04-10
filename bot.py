import asyncio
import logging
from datetime import datetime
import aiosqlite

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db.database import init_db, DB_NAME

# --- КОНФИГ ---
API_TOKEN = '8690428738:AAGUuo-V3id99Z-3UsT6twy2bJGmScCXFbA'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()

# --- МЕНЮ (Reply) ---
def main_menu():
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="📅 Планировщик")],
        [KeyboardButton(text="🌸 Комплимент"), KeyboardButton(text="🆘 Поддержка")],
        [KeyboardButton(text="🔄 Привычки"), KeyboardButton(text="🔒 Приватное")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- РАНГИ ---
def get_rank(streak):
    if streak < 7: return "🌱 Исследователь"
    if streak < 21: return "🔥 Приверженец"
    return "💎 Мастер баланса"

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.from_user.first_name)
        )
        await db.commit()
    await message.answer("✨ Добро пожаловать в систему ЛЮМИ. Твой путь к личной эффективности и гармонии начинается здесь.", reply_markup=main_menu())

# --- ПРОФИЛЬ ---
@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
    
    if row:
        name, streak, joined = row
        rank = get_rank(streak)
        caption = (
            f"👤 **ПРОФИЛЬ: {name.upper()}**\n"
            f"────────────────────\n"
            f"🎖 **Ранг:** {rank}\n"
            f"🔥 **Серия:** {streak} дн.\n"
            f"📅 **С нами с:** {joined[:10]}\n"
            f"────────────────────"
        )
        
        # Исправленные кнопки (обязательно указываем callback_data)
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Достижения", callback_data="dev_btn"), 
             InlineKeyboardButton(text="📊 Статистика", callback_data="dev_btn")],
            [InlineKeyboardButton(text="📝 Редактировать", callback_data="dev_btn"), 
             InlineKeyboardButton(text="🆘 Поддержка", callback_data="dev_btn")]
        ])
        
        try:
            photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
            if photos.total_count > 0:
                await message.answer_photo(photos.photos[0][-1].file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
            else:
                await message.answer(caption, reply_markup=kb, parse_mode="Markdown")
        except:
            await message.answer(caption, reply_markup=kb, parse_mode="Markdown")

# Заглушка для кнопок
@dp.callback_query(F.data == "dev_btn")
async def process_dev_btn(callback: types.CallbackQuery):
    await callback.answer("Эта функция скоро появится! 🛠", show_alert=True)

# --- ПЛАНИРОВЩИК ---
@dp.message(F.text == "📅 Планировщик")
async def plan_start(message: types.Message, state: FSMContext):
    await message.answer("📝 Введи название задачи:")
    await state.set_state(TaskStates.waiting_for_title)

@dp.message(TaskStates.waiting_for_title)
async def plan_name(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📅 Введи время (формат: ДД.ММ ЧЧ:ММ, например 10.04 15:30):")
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
        await message.answer(f"✅ Задача «{data['title']}» сохранена на {message.text}!")
        await state.clear()
    except:
        await message.answer("❌ Ошибка. Пиши строго как в примере: 10.04 15:00")

# --- ФОНОВАЯ ПРОВЕРКА ---
async def check_tasks():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:00")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now,)) as cursor:
            tasks = await cursor.fetchall()
            for tid, uid, title in tasks:
                try:
                    await bot.send_message(uid, f"🔔 **НАПОМИНАНИЕ!**\n\nПора сделать: {title}")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                    await db.commit()
                except:
                    pass

async def main():
    await init_db()
    scheduler.add_job(check_tasks, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

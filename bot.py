import asyncio
import logging
from datetime import datetime
import aiosqlite
import pytz

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
MOSCOW_TZ = pytz.timezone("Europe/Moscow")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
scheduler = AsyncIOScheduler(timezone=MOSCOW_TZ)

class TaskStates(StatesGroup):
    waiting_for_title = State()
    waiting_for_time = State()

# --- КЛАВИАТУРА ---
def main_menu():
    kb = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="🗓 Планировщик")],
        [KeyboardButton(text="🌸 Комплимент"), KeyboardButton(text="🆘 Поддержка")],
        [KeyboardButton(text="🔄 Привычки"), KeyboardButton(text="🔒 Приватное")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

# --- ОБРАБОТЧИКИ ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.from_user.first_name)
        )
        await db.commit()
    await message.answer("✨ Система ЛЮМИ активирована. Готов к работе.", reply_markup=main_menu())

@dp.message(F.text == "👤 Профиль")
async def show_profile(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date FROM users WHERE user_id = ?", (message.from_user.id,)) as cursor:
            row = await cursor.fetchone()
    
    if row:
        name, streak, joined = row
        caption = (
            f"👤 **ПРОФИЛЬ: {name.upper()}**\n"
            f"────────────────────\n"
            f"🎖 **Ранг:** 🌱 Исследователь\n"
            f"🔥 **Серия:** {streak} дн.\n"
            f"📅 **С нами с:** {joined[:10]}\n"
            f"────────────────────"
        )
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🏆 Достижения", callback_data="dev"), InlineKeyboardButton(text="📊 Статистика", callback_data="dev")]
        ])
        
        # Ссылка на картинку-заглушку, если аватара нет
        default_img = "https://i.pinimg.com/originals/f4/d0/20/f4d020819777123910c87f6e07663f7f.jpg"
        
        try:
            photos = await bot.get_user_profile_photos(message.from_user.id, limit=1)
            if photos.total_count > 0:
                await message.answer_photo(photos.photos[0][-1].file_id, caption=caption, reply_markup=kb, parse_mode="Markdown")
            else:
                await message.answer_photo(default_img, caption=caption, reply_markup=kb, parse_mode="Markdown")
        except:
            await message.answer_photo(default_img, caption=caption, reply_markup=kb, parse_mode="Markdown")

@dp.callback_query(F.data == "dev")
async def dev_call(callback: types.CallbackQuery):
    await callback.answer("Скоро будет доступно! 🛠", show_alert=True)

# ПЛАНИРОВЩИК
@dp.message(F.text == "🗓 Планировщик")
async def plan_start(message: types.Message, state: FSMContext):
    await message.answer("📝 Какую задачу поставить?")
    await state.set_state(TaskStates.waiting_for_title)

@dp.message(TaskStates.waiting_for_title)
async def plan_title(message: types.Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("📅 Напиши время (ДД.ММ ЧЧ:ММ):")
    await state.set_state(TaskStates.waiting_for_time)

@dp.message(TaskStates.waiting_for_time)
async def plan_time(message: types.Message, state: FSMContext):
    try:
        # Парсим время и добавляем текущий год
        dt = datetime.strptime(f"{message.text}.{datetime.now().year}", "%d.%m %H:%M.%Y")
        data = await state.get_data()
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO tasks (user_id, title, task_time) VALUES (?, ?, ?)",
                             (message.from_user.id, data['title'], dt.strftime("%Y-%m-%d %H:%M:00")))
            await db.commit()
        await message.answer(f"✅ Ок, напомню: «{data['title']}» в {message.text}")
        await state.clear()
    except:
        await message.answer("❌ Напиши по примеру: 10.04 15:30")

# ФОНОВАЯ ПРОВЕРКА ЗАДАЧ
async def check_tasks():
    # Берем время именно по Москве
    now = datetime.now(MOSCOW_TZ).strftime("%Y-%m-%d %H:%M:00")
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT task_id, user_id, title FROM tasks WHERE task_time <= ? AND is_notified = 0", (now,)) as cursor:
            tasks = await cursor.fetchall()
            for tid, uid, title in tasks:
                try:
                    await bot.send_message(uid, f"🔔 **НАПОМИНАНИЕ:**\n\nПора сделать: **{title}**")
                    await db.execute("UPDATE tasks SET is_notified = 1 WHERE task_id = ?", (tid,))
                    await db.commit()
                except Exception as e:
                    logging.error(f"Failed to send task: {e}")

async def main():
    await init_db()
    # Проверка каждую минуту
    scheduler.add_job(check_tasks, "interval", minutes=1)
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

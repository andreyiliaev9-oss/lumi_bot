import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import aiosqlite

from db.database import init_db, DB_NAME

# Конфиг
API_TOKEN = '8690428738:AAGUuo-V3id99Z-3UsT6twy2bJGmScCXFbA'
ADMIN_ID = 5695627606 # Твой ID для получения сообщений поддержки

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# --- ЛОГИКА РАНГОВ ---
def get_rank(streak):
    if streak < 7: return "🌱 Исследователь"
    if streak < 21: return "🔥 Приверженец"
    if streak < 50: return "💎 Мастер баланса"
    return "👑 Легенда ЛЮМИ"

# --- КЛАВИАТУРЫ ---
def get_profile_kb():
    buttons = [
        [InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📝 Редактировать", callback_data="edit_profile"),
         InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ОБРАБОТЧИКИ КОМАНД ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (message.from_user.id, message.from_user.username, message.from_user.first_name)
        )
        await db.commit()
    await message.answer("✨ Добро пожаловать в ЛЮМИ.\nТвой персональный путь к гармонии начался. Используй /profile для просмотра своей карточки.")

@dp.message(Command("profile"))
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_data = await cursor.fetchone()
            
    if user_data:
        name, streak, joined = user_data
        rank = get_rank(streak)
        
        caption = (
            f"👤 **ПРОФИЛЬ: {name}**\n"
            f"────────────────────\n"
            f"🎖 **Ранг:** {rank}\n"
            f"🔥 **Серия:** {streak} дн.\n"
            f"📅 **С нами с:** {joined[:10]}\n"
            f"────────────────────\n"
            f"Выбери раздел ниже:"
        )

        try:
            photos = await bot.get_user_profile_photos(user_id, limit=1)
            if photos.total_count > 0:
                await message.answer_photo(photos.photos[0][-1].file_id, caption=caption, reply_markup=get_profile_kb(), parse_mode="Markdown")
            else:
                await message.answer(caption, reply_markup=get_profile_kb(), parse_mode="Markdown")
        except:
            await message.answer(caption, reply_markup=get_profile_kb(), parse_mode="Markdown")

# --- ОБРАБОТКА КНОПОК ---
@dp.callback_query(F.data == "support")
async def support_handler(callback: types.CallbackQuery):
    await callback.message.answer("Опиши свою проблему или введи секретный код доступа:")
    await callback.answer()

@dp.callback_query(F.data.in_(["achievements", "stats", "edit_profile"]))
async def placeholder_handler(callback: types.CallbackQuery):
    await callback.answer("Этот раздел в разработке 🛠", show_alert=True)

# --- ПЛАНИРОВЩИК (РАССЫЛКА) ---
async def send_scheduled_messages(mode):
    async with aiosqlite.connect(DB_NAME) as db:
        column_enabled = "morning_enabled" if mode == "morning" else "evening_enabled"
        column_time = "morning_time" if mode == "morning" else "evening_time"
        column_msg = "morning_msg" if mode == "morning" else "evening_msg"
        current_time = datetime.now().strftime("%H:%M")
        
        async with db.execute(f"SELECT user_id, {column_msg} FROM users WHERE {column_enabled} = 1 AND {column_time} = ?", (current_time,)) as cursor:
            users = await cursor.fetchall()
            for user_id, msg in users:
                try:
                    await bot.send_message(user_id, msg)
                except: pass

async def main():
    await init_db()
    scheduler.add_job(send_scheduled_messages, "interval", minutes=1, args=["morning"])
    scheduler.add_job(send_scheduled_messages, "interval", minutes=1, args=["evening"])
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

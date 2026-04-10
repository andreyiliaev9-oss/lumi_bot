from aiogram import F
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, InputFile

# Логика определения ранга
def get_rank(streak):
    if streak < 7: return "🌱 Исследователь"
    if streak < 21: return "🔥 Приверженец"
    if streak < 50: return "💎 Мастер баланса"
    return "👑 Легенда ЛЮМИ"

# Кнопки профиля
def get_profile_kb():
    buttons = [
        [InlineKeyboardButton(text="🏆 Достижения", callback_data="achievements"),
         InlineKeyboardButton(text="📊 Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="📝 Редактировать", callback_data="edit_profile"),
         InlineKeyboardButton(text="🆘 Поддержка", callback_data="support")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

@dp.message(Command("profile"))
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    
    async with aiosqlite.connect(DB_NAME) as db:
        async with db.execute("SELECT first_name, streak_days, joined_date FROM users WHERE user_id = ?", (user_id,)) as cursor:
            user_data = await cursor.fetchone()
            
    if user_data:
        name, streak, joined = user_data
        rank = get_rank(streak)
        
        # Пытаемся получить фото
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        
        caption = (
            f"👤 **Профиль: {name}**\n"
            f"────────────────────\n"
            f"🎖 Ранг: {rank}\n"
            f"🔥 Серия: {streak} дн.\n"
            f"📅 С нами с: {joined[:10]}\n"
            f"────────────────────\n"
            f"Выбери раздел ниже:"
        )

        if photos.total_count > 0:
            await message.answer_photo(photos.photos[0][-1].file_id, caption=caption, reply_markup=get_profile_kb(), parse_mode="Markdown")
        else:
            # Если фото нет, бот присылает свою аватарку (нужен file_id или URL)
            await message.answer(caption, reply_markup=get_profile_kb(), parse_mode="Markdown")

# Обработка кнопки Поддержка
@dp.callback_query(F.data == "support")
async def support_handler(callback: types.CallbackQuery):
    await callback.message.answer("Опиши свою проблему в одном сообщении, и я передам её админу. \n\n*Если у тебя есть секретный код доступа, введи его сейчас.*", parse_mode="Markdown")

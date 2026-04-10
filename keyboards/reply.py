from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_reply_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="✅ Привычки")],
            [KeyboardButton(text="📅 Планировщик"), KeyboardButton(text="🌸 Цикл")],
            [KeyboardButton(text="📔 Дневник"), KeyboardButton(text="🔒 Приватные заметки")],
            [KeyboardButton(text="⚙️ Настройки")]
        ],
        resize_keyboard=True
    )

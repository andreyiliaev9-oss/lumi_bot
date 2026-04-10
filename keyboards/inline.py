from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="✅ Привычки", callback_data="habits")],
        [InlineKeyboardButton(text="📅 Планировщик", callback_data="planner")],
        [InlineKeyboardButton(text="🌸 Цикл", callback_data="cycle")],
        [InlineKeyboardButton(text="📔 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="🔒 Приватные заметки", callback_data="secret_notes")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")]
    ])

def back_button(callback="start"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback)]
    ])

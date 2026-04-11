from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_reply_menu(is_admin: bool = False):
    buttons = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="⚙️ Настройки")],
        [KeyboardButton(text="💝 Комплименты"), KeyboardButton(text="🔒 Приватное")],
    ]
    if is_admin:
        buttons.append([KeyboardButton(text="👑 Админ-панель")])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)

def cancel_reply():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )

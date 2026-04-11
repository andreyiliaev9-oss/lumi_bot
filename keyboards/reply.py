from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def main_kb(user_id: int, admin_id: int):
    buttons = [
        [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="✨ Комплименты")],
        [KeyboardButton(text="🔐 Приватное"), KeyboardButton(text="🆘 Поддержка")]
    ]
    
    # Если это ты, добавляем кнопку админки
    if user_id == admin_id:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])
        
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выбери раздел..."
    )

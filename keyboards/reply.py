from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from config import ADMIN_ID

def main_kb(user_id: int):
    # Основные кнопки для всех пользователей
    buttons = [
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="✨ Комплимент")
        ],
        [
            KeyboardButton(text="🔐 Приватное"),
            KeyboardButton(text="🆘 Поддержка")
        ]
    ]

    # Добавляем кнопку админки только владельцу
    if user_id == ADMIN_ID:
        buttons.append([KeyboardButton(text="⚙️ Админ-панель")])

    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        input_field_placeholder="Выберите раздел меню..."
    )

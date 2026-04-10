from aiogram.utils.keyboard import ReplyKeyboardBuilder, KeyboardButton
from aiogram.types import ReplyKeyboardMarkup


def main_menu() -> ReplyKeyboardMarkup:
    """
    Создает главное меню бота.
    """
    builder = ReplyKeyboardBuilder()
    
    builder.add(
        KeyboardButton(text="👤 Профиль"),
        KeyboardButton(text="🔄 Привычки"),
        KeyboardButton(text="📅 Планировщик"),
        KeyboardButton(text="🌸 Комплимент"),  # Новая кнопка!
        KeyboardButton(text="🔒 Приватное"),
        KeyboardButton(text="✉️ Поддержка")
    )
    
    # Распределяем кнопки: 3 в первом ряду, 3 во втором (ровный квадрат)
    builder.adjust(3, 3)

    return builder.as_markup(
        resize_keyboard=True, 
        input_field_placeholder="Выбери раздел меню..."
    )

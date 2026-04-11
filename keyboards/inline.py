from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню админки
def admin_main_kb():
    buttons = [
        [InlineKeyboardButton(text="❤️ Комплименты", callback_data="admin_compliments")],
        [InlineKeyboardButton(text="🧬 Советы цикла", callback_data="admin_cycle_tips")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔑 Сброс PIN", callback_data="admin_pin_manage")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Подменю для комплиментов
def admin_compliments_kb():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_compliment")],
        [InlineKeyboardButton(text="🗑 Удалить все (сброс)", callback_data="clear_compliments")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_stats")] # Возврат в главную админку
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def back_button(callback="start"):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data=callback)]
    ])

def private_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Планировщик", callback_data="planner")],
        [InlineKeyboardButton(text="🌸 Цикл", callback_data="cycle")],
        [InlineKeyboardButton(text="📔 Дневник", callback_data="diary")],
        [InlineKeyboardButton(text="📝 Заметки", callback_data="secret_notes")],
        [InlineKeyboardButton(text="📦 Капсула времени", callback_data="time_capsule")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
    ])

def habit_frequency_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Ежедневно", callback_data="freq_everyday")],
        [InlineKeyboardButton(text="📆 Пн, Ср, Пт", callback_data="freq_135")],
        [InlineKeyboardButton(text="📆 Вт, Чт", callback_data="freq_24")],
        [InlineKeyboardButton(text="📆 Сб, Вс", callback_data="freq_67")],
        [InlineKeyboardButton(text="🔢 По числам месяца", callback_data="freq_month_days")],
        [InlineKeyboardButton(text="⚙️ Свои дни", callback_data="freq_custom")]
    ])

def cycle_phases_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🩸 Месячные", callback_data="phase_menstruation")],
        [InlineKeyboardButton(text="🌱 Фолликулярная", callback_data="phase_follicular")],
        [InlineKeyboardButton(text="🥚 Овуляция", callback_data="phase_ovulation")],
        [InlineKeyboardButton(text="🌙 Лютеиновая", callback_data="phase_luteal")]
    ])

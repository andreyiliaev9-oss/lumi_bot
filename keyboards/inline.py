from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- АДМИН ПАНЕЛЬ ---
def admin_main_kb():
    buttons = [
        [InlineKeyboardButton(text="❤️ Комплименты", callback_data="admin_compliments")],
        [InlineKeyboardButton(text="🧬 Советы цикла", callback_data="admin_cycle_tips")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⏰ Время сообщ.", callback_data="admin_time_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔑 Сброс PIN", callback_data="admin_pin_manage")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def admin_compliments_kb():
    buttons = [
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_compliment")],
        [InlineKeyboardButton(text="🗑 Удалить все (сброс)", callback_data="clear_compliments")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_main")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# --- ПРИВАТНАЯ ЗОНА (СЕЙФ) ---
def pin_keyboard(current_pin: str = ""):
    # Отображаем звездочки вместо цифр сверху кнопок
    display = "● " * len(current_pin) if current_pin else "Введите PIN"
    
    builder = [
        [InlineKeyboardButton(text=display, callback_data="none")],
        [
            InlineKeyboardButton(text="1", callback_data="pin_1"),
            InlineKeyboardButton(text="2", callback_data="pin_2"),
            InlineKeyboardButton(text="3", callback_data="pin_3")
        ],
        [
            InlineKeyboardButton(text="4", callback_data="pin_4"),
            InlineKeyboardButton(text="5", callback_data="pin_5"),
            InlineKeyboardButton(text="6", callback_data="pin_6")
        ],
        [
            InlineKeyboardButton(text="7", callback_data="pin_7"),
            InlineKeyboardButton(text="8", callback_data="pin_8"),
            InlineKeyboardButton(text="9", callback_data="pin_9")
        ],
        [
            InlineKeyboardButton(text="❌", callback_data="pin_clear"),
            InlineKeyboardButton(text="0", callback_data="pin_0"),
            InlineKeyboardButton(text="⬅️", callback_data="pin_backspace")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=builder)

def private_main_menu_kb():
    buttons = [
        [InlineKeyboardButton(text="📅 Планировщик", callback_data="p_planner")],
        [InlineKeyboardButton(text="🌸 Трекер цикла", callback_data="p_cycle")],
        [InlineKeyboardButton(text="📖 Личный дневник", callback_data="p_diary")],
        [InlineKeyboardButton(text="📝 Приватные заметки", callback_data="p_notes")],
        [InlineKeyboardButton(text="⏳ Капсула времени", callback_data="p_capsule")],
        [InlineKeyboardButton(text="🚪 Выйти в меню", callback_data="p_exit")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

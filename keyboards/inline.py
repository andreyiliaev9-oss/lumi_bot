from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# --- АДМИН-ПАНЕЛЬ ---
def admin_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="❤️ Комплименты", callback_data="admin_compliments")],
        [InlineKeyboardButton(text="🧬 Советы цикла", callback_data="admin_cycle_tips")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="⏰ Время сообщ.", callback_data="admin_time_settings")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔑 Сброс PIN", callback_data="admin_pin_manage")]
    ])

def admin_compliments_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить", callback_data="add_compliment")],
        [InlineKeyboardButton(text="🗑 Удалить всё", callback_data="clear_compliments")],
        [InlineKeyboardButton(text="« Назад", callback_data="admin_main")]
    ])

# --- ПРИВАТНАЯ ЗОНА: ВВОД PIN ---
def pin_keyboard(current_pin: str = ""):
    # Показываем точки вместо цифр для красоты и секретности
    display = "● " * len(current_pin) if current_pin else "Введите PIN"
    
    builder = [[InlineKeyboardButton(text=display, callback_data="none")]]
    
    # Сетка цифр
    rows = [["1","2","3"], ["4","5","6"], ["7","8","9"]]
    for row in rows:
        builder.append([InlineKeyboardButton(text=c, callback_data=f"pin_{c}") for c in row])
    
    builder.append([
        InlineKeyboardButton(text="❌", callback_data="pin_clear"),
        InlineKeyboardButton(text="0", callback_data="pin_0"),
        InlineKeyboardButton(text="⬅️", callback_data="pin_backspace")
    ])
    return InlineKeyboardMarkup(inline_keyboard=builder)

# --- МЕНЮ ВНУТРИ ПРИВАТКИ ---
def private_main_menu_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📅 Планировщик", callback_data="p_planner")],
        [InlineKeyboardButton(text="🌸 Трекер цикла", callback_data="p_cycle")],
        [InlineKeyboardButton(text="📖 Личный дневник", callback_data="p_diary")],
        [InlineKeyboardButton(text="📝 Приватные заметки", callback_data="p_notes")],
        [InlineKeyboardButton(text="⏳ Капсула времени", callback_data="p_capsule")],
        [InlineKeyboardButton(text="🚪 Выйти", callback_data="p_exit")]
    ])

# --- МЕНЮ ЦИКЛА ---
def cycle_main_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Отметить состояние", callback_data="cycle_log")],
        [InlineKeyboardButton(text="⚙️ Настроить цикл", callback_data="cycle_setup")],
        [InlineKeyboardButton(text="📊 Статистика (CSV)", callback_data="cycle_export")],
        [InlineKeyboardButton(text="« Назад", callback_data="p_main")]
    ])

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
# ============== REPLY KEYBOARDS ==============
def main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👤 Профиль"), KeyboardButton(text="✅ Привычки")],
            [KeyboardButton(text="📅 Планировщик"), KeyboardButton(text="🔒 Личное")],
            [KeyboardButton(text="🌙 Цикл"), KeyboardButton(text="⚙️ Настройки")],
        ],
        resize_keyboard=True
    )
def back_keyboard() -> ReplyKeyboardMarkup:
    """Кнопка назад"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="◀️ Назад")]],
        resize_keyboard=True
    )
def confirm_keyboard() -> ReplyKeyboardMarkup:
    """Подтверждение"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")],
        ],
        resize_keyboard=True
    )
def cancel_keyboard() -> ReplyKeyboardMarkup:
    """Отмена действия"""
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True
    )
# ============== INLINE KEYBOARDS ==============
def profile_inline_keyboard() -> InlineKeyboardMarkup:
    """Inline клавиатура профиля"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Статистика", callback_data="profile_stats")],
            [InlineKeyboardButton(text="📖 Дневник", callback_data="profile_diary")],
            [InlineKeyboardButton(text="🏆 Достижения", callback_data="profile_achievements")],
        ]
    )
def habits_inline_keyboard(habits: list) -> InlineKeyboardMarkup:
    """Список привычек с действиями"""
    buttons = []
    for habit in habits:
        buttons.append([
            InlineKeyboardButton(text=f"✅ {habit.name}", callback_data=f"habit_complete_{habit.id}"),
            InlineKeyboardButton(text="📝", callback_data=f"habit_edit_{habit.id}"),
            InlineKeyboardButton(text="🗑", callback_data=f"habit_delete_{habit.id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="➕ Добавить привычку", callback_data="habit_add")])
    buttons.append([InlineKeyboardButton(text="📊 Статистика привычек", callback_data="habits_stats")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def habit_actions_keyboard(habit_id: int) -> InlineKeyboardMarkup:
    """Действия с привычкой"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"habit_complete_{habit_id}")],
            [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"habit_skip_{habit_id}")],
            [InlineKeyboardButton(text="🔕 Отключить на сегодня", callback_data=f"habit_disable_{habit_id}")],
        ]
    )
def habit_reminder_keyboard() -> InlineKeyboardMarkup:
    """Настройка напоминаний привычки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📅 По дням недели", callback_data="habit_reminder_days")],
            [InlineKeyboardButton(text="⏰ Ежедневно", callback_data="habit_reminder_daily")],
            [InlineKeyboardButton(text="🔄 Повтор каждый час", callback_data="habit_reminder_hourly")],
            [InlineKeyboardButton(text="❌ Без напоминаний", callback_data="habit_reminder_none")],
        ]
    )
def days_of_week_keyboard() -> InlineKeyboardMarkup:
    """Выбор дней недели"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Пн", callback_data="day_1"),
                InlineKeyboardButton(text="Вт", callback_data="day_2"),
                InlineKeyboardButton(text="Ср", callback_data="day_3"),
                InlineKeyboardButton(text="Чт", callback_data="day_4"),
            ],
            [
                InlineKeyboardButton(text="Пт", callback_data="day_5"),
                InlineKeyboardButton(text="Сб", callback_data="day_6"),
                InlineKeyboardButton(text="Вс", callback_data="day_7"),
            ],
            [InlineKeyboardButton(text="✅ Готово", callback_data="days_done")],
        ]
    )
def events_inline_keyboard(events: list) -> InlineKeyboardMarkup:
    """Список событий"""
    buttons = []
    for event in events:
        date_str = event.event_date.strftime("%d.%m")
        buttons.append([
            InlineKeyboardButton(
                text=f"📅 {event.title} ({date_str})", 
                callback_data=f"event_view_{event.id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text="➕ Добавить событие", callback_data="event_add")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)
def event_actions_keyboard(event_id: int) -> InlineKeyboardMarkup:
    """Действия с событием"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"event_complete_{event_id}")],
            [InlineKeyboardButton(text="⏭ Перенести", callback_data=f"event_postpone_{event_id}")],
            [InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"event_skip_{event_id}")],
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"event_edit_{event_id}")],
            [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"event_delete_{event_id}")],
        ]
    )
def event_notifications_keyboard() -> InlineKeyboardMarkup:
    """Выбор уведомлений для события"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="24ч", callback_data="notif_24"),
                InlineKeyboardButton(text="12ч", callback_data="notif_12"),
            ],
            [
                InlineKeyboardButton(text="7ч", callback_data="notif_7"),
                InlineKeyboardButton(text="5ч", callback_data="notif_5"),
            ],
            [
                InlineKeyboardButton(text="3ч", callback_data="notif_3"),
                InlineKeyboardButton(text="1ч", callback_data="notif_1"),
            ],
            [InlineKeyboardButton(text="✅ Готово", callback_data="notif_done")],
        ]
    )
# PIN-клавиатура
def pin_keyboard() -> InlineKeyboardMarkup:
    """PIN-клавиатура"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1", callback_data="pin_1"),
                InlineKeyboardButton(text="2", callback_data="pin_2"),
                InlineKeyboardButton(text="3", callback_data="pin_3"),
            ],
            [
                InlineKeyboardButton(text="4", callback_data="pin_4"),
                InlineKeyboardButton(text="5", callback_data="pin_5"),
                InlineKeyboardButton(text="6", callback_data="pin_6"),
            ],
            [
                InlineKeyboardButton(text="7", callback_data="pin_7"),
                InlineKeyboardButton(text="8", callback_data="pin_8"),
                InlineKeyboardButton(text="9", callback_data="pin_9"),
            ],
            [
                InlineKeyboardButton(text="⌫", callback_data="pin_back"),
                InlineKeyboardButton(text="0", callback_data="pin_0"),
                InlineKeyboardButton(text="✓", callback_data="pin_confirm"),
            ],
        ]
    )
def private_section_keyboard() -> InlineKeyboardMarkup:
    """Приватный раздел"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📝 Записи", callback_data="private_entries")],
            [InlineKeyboardButton(text="➕ Новая запись", callback_data="private_new")],
            [InlineKeyboardButton(text="🔐 Сменить PIN", callback_data="private_change_pin")],
            [InlineKeyboardButton(text="🚪 Выход", callback_data="private_exit")],
        ]
    )
def cycle_main_keyboard() -> InlineKeyboardMarkup:
    """Главное меню цикла"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📊 Мой цикл", callback_data="cycle_status")],
            [InlineKeyboardButton(text="📝 Новая запись", callback_data="cycle_log")],
            [InlineKeyboardButton(text="📅 Обновить дату", callback_data="cycle_update")],
            [InlineKeyboardButton(text="📖 Статистика", callback_data="cycle_stats")],
            [InlineKeyboardButton(text="💡 Советы", callback_data="cycle_tips")],
        ]
    )
def cycle_phase_keyboard(phase: str) -> InlineKeyboardMarkup:
    """Информация о фазе цикла"""
    tips_btn = InlineKeyboardButton(text="💡 Советы", callback_data=f"cycle_tip_{phase}")
    log_btn = InlineKeyboardButton(text="📝 Самочувствие", callback_data="cycle_log")
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [tips_btn],
            [log_btn],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="cycle_back")],
        ]
    )
def cycle_wellness_keyboard() -> InlineKeyboardMarkup:
    """Оценка самочувствия"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="1", callback_data="wellness_mood_1"),
                InlineKeyboardButton(text="2", callback_data="wellness_mood_2"),
                InlineKeyboardButton(text="3", callback_data="wellness_mood_3"),
                InlineKeyboardButton(text="4", callback_data="wellness_mood_4"),
                InlineKeyboardButton(text="5", callback_data="wellness_mood_5"),
            ],
            [InlineKeyboardButton(text="Настроение", callback_data="wellness_label_mood")],
            [
                InlineKeyboardButton(text="1", callback_data="wellness_pain_1"),
                InlineKeyboardButton(text="2", callback_data="wellness_pain_2"),
                InlineKeyboardButton(text="3", callback_data="wellness_pain_3"),
                InlineKeyboardButton(text="4", callback_data="wellness_pain_4"),
                InlineKeyboardButton(text="5", callback_data="wellness_pain_5"),
            ],
            [InlineKeyboardButton(text="Боль", callback_data="wellness_label_pain")],
            [
                InlineKeyboardButton(text="1", callback_data="wellness_energy_1"),
                InlineKeyboardButton(text="2", callback_data="wellness_energy_2"),
                InlineKeyboardButton(text="3", callback_data="wellness_energy_3"),
                InlineKeyboardButton(text="4", callback_data="wellness_energy_4"),
                InlineKeyboardButton(text="5", callback_data="wellness_energy_5"),
            ],
            [InlineKeyboardButton(text="Энергия", callback_data="wellness_label_energy")],
            [
                InlineKeyboardButton(text="1", callback_data="wellness_sleep_1"),
                InlineKeyboardButton(text="2", callback_data="wellness_sleep_2"),
                InlineKeyboardButton(text="3", callback_data="wellness_sleep_3"),
                InlineKeyboardButton(text="4", callback_data="wellness_sleep_4"),
                InlineKeyboardButton(text="5", callback_data="wellness_sleep_5"),
            ],
            [InlineKeyboardButton(text="Сон", callback_data="wellness_label_sleep")],
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="wellness_save")],
        ]
    )
def settings_keyboard() -> InlineKeyboardMarkup:
    """Настройки"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔔 Уведомления", callback_data="settings_notifications")],
            [InlineKeyboardButton(text="🌙 Тихий режим", callback_data="settings_quiet")],
            [InlineKeyboardButton(text="📊 Экспорт данных", callback_data="settings_export")],
            [InlineKeyboardButton(text="❓ Помощь", callback_data="settings_help")],
        ]
    )
def notifications_settings_keyboard(user) -> InlineKeyboardMarkup:
    """Настройки уведомлений"""
    habit_status = "✅" if user.habit_notifications else "❌"
    planner_status = "✅" if user.planner_notifications else "❌"
    cycle_status = "✅" if user.cycle_notifications else "❌"
    morning_status = "✅" if user.morning_night_notifications else "❌"
    global_status = "✅" if user.notifications_enabled else "❌"
    
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"{habit_status} Привычки", callback_data="notif_toggle_habits")],
            [InlineKeyboardButton(text=f"{planner_status} Планировщик", callback_data="notif_toggle_planner")],
            [InlineKeyboardButton(text=f"{cycle_status} Цикл", callback_data="notif_toggle_cycle")],
            [InlineKeyboardButton(text=f"{morning_status} Утро/Ночь", callback_data="notif_toggle_morning")],
            [InlineKeyboardButton(text=f"{global_status} Все уведомления", callback_data="notif_toggle_global")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="settings_back")],
        ]
    )
def quiet_mode_keyboard() -> InlineKeyboardMarkup:
    """Настройка тихого режима"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🌙 Начало (22:00)", callback_data="quiet_start")],
            [InlineKeyboardButton(text="☀️ Конец (09:00)", callback_data="quiet_end")],
            [InlineKeyboardButton(text="❌ Отключить", callback_data="quiet_disable")],
            [InlineKeyboardButton(text="✅ Сохранить", callback_data="quiet_save")],
        ]
    )
# Admin keyboards
def admin_keyboard() -> InlineKeyboardMarkup:
    """Админ панель"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📨 Рассылка", callback_data="admin_broadcast")],
            [InlineKeyboardButton(text="☀️ Утренние сообщения", callback_data="admin_morning")],
            [InlineKeyboardButton(text="🌙 Ночные сообщения", callback_data="admin_night")],
            [InlineKeyboardButton(text="💡 Советы цикла", callback_data="admin_tips")],
            [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        ]
    )
def admin_morning_night_keyboard(msg_type: str) -> InlineKeyboardMarkup:
    """Управление утренними/ночными сообщениями"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="➕ Добавить", callback_data=f"admin_{msg_type}_add")],
            [InlineKeyboardButton(text="📋 Список", callback_data=f"admin_{msg_type}_list")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_back")],
        ]
    )

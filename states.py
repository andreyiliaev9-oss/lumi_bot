from aiogram.fsm.state import State, StatesGroup
# Привычки
class HabitStates(StatesGroup):
    waiting_name = State()
    waiting_description = State()
    waiting_reminder_time = State()
    waiting_reminder_days = State()
    editing = State()
# Планировщик
class EventStates(StatesGroup):
    waiting_title = State()
    waiting_description = State()
    waiting_date = State()
    waiting_time = State()
    waiting_notifications = State()
    waiting_postpone_date = State()
    editing = State()
# Личное (PIN)
class PrivateStates(StatesGroup):
    waiting_pin_enter = State()
    waiting_pin_new = State()
    waiting_pin_confirm = State()
    waiting_recovery = State()
    in_private_section = State()
    waiting_entry_content = State()
    waiting_entry_edit = State()
# Цикл
class CycleStates(StatesGroup):
    waiting_period_start = State()
    waiting_cycle_length = State()
    waiting_period_length = State()
    logging_wellness = State()
    waiting_notes = State()
# Настройки
class SettingsStates(StatesGroup):
    waiting_quiet_start = State()
    waiting_quiet_end = State()
# Админ
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_morning_time = State()
    waiting_morning_content = State()
    waiting_night_time = State()
    waiting_night_content = State()
    waiting_tip_phase = State()
    waiting_tip_content = State()
# Общие
class CommonStates(StatesGroup):
    onboarding = State()

import io
import csv
from datetime import datetime, date, timedelta
from calendar import monthcalendar

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter  # Важно для работы состояний
from sqlalchemy import select

# Предполагаем, что импорты ниже верны в вашей структуре проекта
# from db.db import async_session
# from db.models import User, CycleLog, CycleTip
# from keyboards.inline import back_button

router = Router()

# --- Состояния ---
class CycleForm(StatesGroup):
    start_date = State()
    cycle_length = State()
    period_length = State()

class FeelingForm(StatesGroup):
    mood = State()
    pain = State()
    energy = State()
    sleep = State()
    headache = State()
    bloating = State()
    acne = State()
    notes = State()

# --- Вспомогательные функции ---
def get_phase_key(cycle_day: int, period_length: int) -> str:
    if cycle_day <= period_length:
        return "menstruation"
    elif cycle_day <= 14:
        return "follicular"
    elif cycle_day <= 16:
        return "ovulation"
    else:
        return "luteal"

def get_phase_emoji(phase: str) -> str:
    return {"menstruation": "🩸", "follicular": "🌱", "ovulation": "🥚", "luteal": "🌙"}.get(phase, "📌")

# --- Основное меню ---
@router.callback_query(F.data == "cycle")
async def cycle_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear() # Сбрасываем состояния при входе в главное меню
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        
        if not user or not user.cycle_start_date:
            text = "🌸 Трекер цикла не настроен.\nУкажите дату начала последних месячных."
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 Настроить цикл", callback_data="setup_cycle")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
            return

        today = date.today()
        # Расчет текущего дня цикла
        delta = (today - user.cycle_start_date).days
        cycle_day = (delta % user.cycle_length) + 1
        phase_key = get_phase_key(cycle_day, user.period_length)
        phase_emoji = get_phase_emoji(phase_key)

        tip_record = await session.scalar(
            select(CycleTip).where(CycleTip.phase == phase_key, CycleTip.is_active == True)
        )
        advice = tip_record.tip if tip_record else "Будьте внимательны к своему организму."

        # Расчет следующего периода
        current_cycle_start = today - timedelta(days=cycle_day-1)
        next_period = current_cycle_start + timedelta(days=user.cycle_length)
        days_left = (next_period - today).days

        text = (
            f"{phase_emoji} <b>День цикла: {cycle_day}</b>\n"
            f"📌 Фаза: {phase_key.capitalize()}\n"
            f"📅 Следующие месячные: {next_period.strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось дней: {max(0, days_left)}\n"
            f"💡 Совет: {advice}\n\n"
            "Выберите действие:"
        )
        
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="😊 Отметить самочувствие", callback_data="log_feeling")],
            [InlineKeyboardButton(text="📊 Статистика", callback_data="cycle_stats")],
            [InlineKeyboardButton(text="📅 График цикла", callback_data="cycle_calendar")],
            [InlineKeyboardButton(text="📎 Экспорт CSV", callback_data="export_cycle_data")],
            [InlineKeyboardButton(text="💡 Все советы", callback_data="all_tips")],
            [InlineKeyboardButton(text="⚙️ Изменить настройки", callback_data="setup_cycle")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
        ])
        
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception: # Если текст не изменился
            pass
    await callback.answer()

# --- Логика регистрации настроек ---
@router.callback_query(F.data == "setup_cycle")
async def setup_cycle_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите дату начала последних месячных в формате <b>ДД.ММ.ГГГГ</b>:")
    await state.set_state(CycleForm.start_date)
    await callback.answer()

@router.message(CycleForm.start_date)
async def get_start_date(message: Message, state: FSMContext):
    try:
        start = datetime.strptime(message.text, "%d.%m.%Y").date()
        if start > date.today():
            await message.answer("⚠️ Дата не может быть в будущем.")
            return
        await state.update_data(start_date=start)
        await message.answer("Введите среднюю длительность цикла (в днях, обычно 28):")
        await state.set_state(CycleForm.cycle_length)
    except ValueError:
        await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ")

# ... (остальные шаги настройки аналогично, следите за await state.set_state)

# --- Логика опроса самочувствия ---
@router.callback_query(F.data == "log_feeling")
async def log_feeling_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"mood_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Оцените настроение (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.mood)
    await callback.answer()

# Важно: используем StateFilter для корректного перехвата колбэков в состоянии
@router.callback_query(StateFilter(FeelingForm.mood), F.data.startswith("mood_"))
async def get_mood(callback: CallbackQuery, state: FSMContext):
    mood = int(callback.data.split("_")[1])
    await state.update_data(mood=mood)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"pain_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Уровень боли (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.pain)
    await callback.answer()

# ... Повторите паттерн для pain, energy, sleep ...

@router.callback_query(StateFilter(FeelingForm.sleep), F.data.startswith("sleep_"))
async def get_sleep(callback: CallbackQuery, state: FSMContext):
    sleep = int(callback.data.split("_")[1])
    await state.update_data(sleep=sleep)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤕 Головная боль", callback_data="headache_yes"),
         InlineKeyboardButton(text="✅ Нет", callback_data="headache_no")]
    ])
    await callback.message.edit_text("Есть ли головная боль?", reply_markup=kb)
    await state.set_state(FeelingForm.headache)
    await callback.answer()

# Для симптомов ДА/НЕТ
@router.callback_query(StateFilter(FeelingForm.headache), F.data.startswith("headache_"))
async def get_headache(callback: CallbackQuery, state: FSMContext):
    val = "yes" in callback.data
    await state.update_data(headache=val)
    
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤰 Вздутие", callback_data="bloating_yes"),
         InlineKeyboardButton(text="✅ Нет", callback_data="bloating_no")]
    ])
    await callback.message.edit_text("Беспокоит вздутие?", reply_markup=kb)
    await state.set_state(FeelingForm.bloating)
    await callback.answer()

# ... и так далее до заметок ...

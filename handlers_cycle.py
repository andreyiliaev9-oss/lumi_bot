from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import database as db
from config import settings
from keyboards import *
from states import CycleStates
from handlers import main_menu_keyboard, get_user_data
router = Router()
# ============== ЦИКЛ (ТРЕКЕР) ==============
def get_cycle_phase(day_of_cycle: int, cycle_length: int = 28) -> tuple:
    """Определение фазы цикла и описания"""
    if day_of_cycle <= 5:
        return "menstruation", "🩸 Менструация", "Период менструации. Отдохни и позаботься о себе."
    elif day_of_cycle <= 13:
        return "follicular", "🌱 Фолликулярная фаза", "Энергия возвращается. Хорошее время для новых начинаний."
    elif day_of_cycle <= 16:
        return "ovulation", "🥚 Овуляция", "Пик фертильности. Максимум энергии и привлекательности!"
    else:
        return "luteal", "🌙 Лютеиновая фаза", "Подготовка к новому циклу. Возможна усталость."
@router.message(F.text == "🌙 Цикл")
async def show_cycle(message: Message):
    """Показать трекер цикла"""
    user = await db.get_user(message.from_user.id)
    tracker = await db.get_or_create_cycle_tracker(user.id)
    
    if not tracker.last_period_start:
        await message.answer(
            "🌙 <b>Трекер цикла</b>\n\n"
            "У тебя пока не настроен трекер.\n\n"
            "Давай настроим:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="⚙️ Настроить цикл", callback_data="cycle_setup")]
                ]
            )
        )
        return
    
    # Расчёт текущего дня цикла
    days_since_start = (datetime.utcnow() - tracker.last_period_start).days
    current_day = (days_since_start % tracker.cycle_length) + 1
    
    phase_id, phase_name, phase_desc = get_cycle_phase(current_day, tracker.cycle_length)
    
    # Расчёт следующей менструации
    next_period = tracker.last_period_start + timedelta(days=tracker.cycle_length)
    days_until = (next_period - datetime.utcnow()).days
    
    # Расчёт овуляции
    ovulation_date = tracker.last_period_start + timedelta(days=tracker.cycle_length - 14)
    days_to_ovulation = (ovulation_date - datetime.utcnow()).days
    
    text = (
        f"🌙 <b>Твой цикл</b>\n\n"
        f"📊 День цикла: <b>{current_day}/{tracker.cycle_length}</b>\n"
        f"{phase_name}\n\n"
        f"📝 {phase_desc}\n\n"
        f"📅 Следующая менструация:\n"
        f"{next_period.strftime('%d.%m.%Y')} (через {days_until} дней)\n\n"
        f"🥚 Овуляция:\n"
    )
    
    if days_to_ovulation > 0:
        text += f"{ovulation_date.strftime('%d.%m.%Y')} (через {days_to_ovulation} дней)\n"
    elif days_to_ovulation == 0:
        text += "Сегодня! 🎉\n"
    else:
        text += f"Была {abs(days_to_ovulation)} дней назад\n"
    
    await message.answer(text, reply_markup=cycle_main_keyboard())
@router.callback_query(F.data == "cycle_setup")
async def cycle_setup_start(callback: CallbackQuery, state: FSMContext):
    """Начало настройки цикла"""
    await state.set_state(CycleStates.waiting_period_start)
    await callback.message.edit_text(
        "⚙️ <b>Настройка цикла</b>\n\n"
        "Введи дату начала последней менструации (ДД.ММ.ГГГГ):\n\n"
        "Например: 01.12.2024"
    )
    await callback.answer()
@router.message(StateFilter(CycleStates.waiting_period_start))
async def cycle_period_start_received(message: Message, state: FSMContext):
    """Получена дата начала цикла"""
    try:
        date = datetime.strptime(message.text, "%d.%m.%Y")
        if date > datetime.utcnow():
            await message.answer("❌ Дата не может быть в будущем. Введи другую дату:")
            return
        
        await state.update_data(period_start=date)
        await state.set_state(CycleStates.waiting_cycle_length)
        await message.answer(
            "📊 Введи длительность цикла в днях (обычно 28):\n\n"
            "Если не знаешь - напиши 28"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Введи дату как ДД.ММ.ГГГГ:")
@router.message(StateFilter(CycleStates.waiting_cycle_length))
async def cycle_length_received(message: Message, state: FSMContext):
    """Получена длительность цикла"""
    try:
        cycle_length = int(message.text)
        if not (20 <= cycle_length <= 45):
            await message.answer("❌ Неверное значение. Введи число от 20 до 45:")
            return
        
        await state.update_data(cycle_length=cycle_length)
        await state.set_state(CycleStates.waiting_period_length)
        await message.answer(
            "🩸 Введи длительность менструации в днях (обычно 3-7):\n\n"
            "Например: 5"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Введи число:")
@router.message(StateFilter(CycleStates.waiting_period_length))
async def cycle_period_length_received(message: Message, state: FSMContext):
    """Получена длительность менструации"""
    try:
        period_length = int(message.text)
        if not (1 <= period_length <= 10):
            await message.answer("❌ Неверное значение. Введи число от 1 до 10:")
            return
        
        data = await state.get_data()
        user = await db.get_user(message.from_user.id)
        
        await db.update_cycle_tracker(
            user_id=user.id,
            last_period_start=data["period_start"],
            cycle_length=data["cycle_length"],
            period_length=period_length
        )
        
        await state.clear()
        await message.answer(
            "✅ Трекер цикла настроен!\n\n"
            f"📅 Дата начала: {data['period_start'].strftime('%d.%m.%Y')}\n"
            f"📊 Длительность цикла: {data['cycle_length']} дней\n"
            f"🩸 Длительность менструации: {period_length} дней\n\n"
            "Я буду напоминать о важных днях!",
            reply_markup=main_menu_keyboard()
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат. Введи число:")
@router.callback_query(F.data == "cycle_status")
async def cycle_status(callback: CallbackQuery):
    """Показать статус цикла"""
    await callback.message.delete()
    await show_cycle(callback.message)
    await callback.answer()
@router.callback_query(F.data == "cycle_log")
async def cycle_log_start(callback: CallbackQuery, state: FSMContext):
    """Начало записи самочувствия"""
    await state.set_state(CycleStates.logging_wellness)
    get_user_data(callback.from_user.id)["wellness"] = {}
    
    await callback.message.edit_text(
        "📝 <b>Самочувствие</b>\n\n"
        "Оцени по шкале 1-5:\n\n"
        "1 = очень плохо, 5 = отлично",
        reply_markup=cycle_wellness_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data.startswith("wellness_"), StateFilter(CycleStates.logging_wellness))
async def wellness_selected(callback: CallbackQuery, state: FSMContext):
    """Выбрана оценка самочувствия"""
    parts = callback.data.split("_")
    
    if parts[1] == "label":
        await callback.answer()
        return
    
    if parts[1] == "save":
        # Сохраняем запись
        user = await db.get_user(callback.from_user.id)
        wellness_data = get_user_data(callback.from_user.id).get("wellness", {})
        
        async with db.async_session() as session:
            log = db.CycleLog(
                user_id=user.id,
                mood=wellness_data.get("mood"),
                pain=wellness_data.get("pain"),
                energy=wellness_data.get("energy"),
                sleep=wellness_data.get("sleep")
            )
            session.add(log)
            await session.commit()
        
        await state.clear()
        await callback.message.edit_text(
            "✅ Запись самочувствия сохранена!\n\n"
            "Спасибо за заботу о себе! 💚"
        )
        await callback.answer()
        return
    
    # Сохраняем оценку
    metric = parts[1]
    value = int(parts[2])
    
    get_user_data(callback.from_user.id)["wellness"][metric] = value
    await callback.answer(f"{metric.capitalize()}: {value}")
@router.callback_query(F.data == "cycle_update")
async def cycle_update_start(callback: CallbackQuery, state: FSMContext):
    """Обновить дату начала цикла"""
    await state.set_state(CycleStates.waiting_period_start)
    await callback.message.edit_text(
        "📅 <b>Обновление цикла</b>\n\n"
        "Введи дату начала последней менструации (ДД.ММ.ГГГГ):"
    )
    await callback.answer()
@router.callback_query(F.data == "cycle_stats")
async def cycle_stats(callback: CallbackQuery):
    """Статистика цикла"""
    user = await db.get_user(callback.from_user.id)
    tracker = user.cycle_tracker
    logs = user.cycle_logs[-30:]  # Последние 30 записей
    
    if not logs:
        await callback.answer("Нет данных")
        await callback.message.edit_text(
            "📊 Пока нет записей самочувствия.\n\n"
            "Начни отслеживать сегодня!",
            reply_markup=cycle_main_keyboard()
        )
        return
    
    # Расчёт средних значений
    avg_mood = sum(l.mood or 0 for l in logs) / len([l for l in logs if l.mood])
    avg_pain = sum(l.pain or 0 for l in logs) / len([l for l in logs if l.pain])
    avg_energy = sum(l.energy or 0 for l in logs) / len([l for l in logs if l.energy])
    
    text = (
        f"📊 <b>Статистика цикла</b>\n\n"
        f"Всего записей: {len(user.cycle_logs)}\n"
        f"За последние 30 дней: {len(logs)}\n\n"
        f"<b>Средние значения:</b>\n"
        f"Настроение: {avg_mood:.1f}/5\n"
        f"Боль: {avg_pain:.1f}/5\n"
        f"Энергия: {avg_energy:.1f}/5\n"
    )
    
    await callback.message.edit_text(text, reply_markup=cycle_main_keyboard())
    await callback.answer()
@router.callback_query(F.data == "cycle_tips")
async def cycle_tips(callback: CallbackQuery):
    """Советы по циклу"""
    user = await db.get_user(callback.from_user.id)
    tracker = user.cycle_tracker
    
    if tracker and tracker.last_period_start:
        days_since_start = (datetime.utcnow() - tracker.last_period_start).days
        current_day = (days_since_start % tracker.cycle_length) + 1
        phase_id, phase_name, phase_desc = get_cycle_phase(current_day, tracker.cycle_length)
    else:
        phase_id = "general"
        phase_name = "Общие советы"
        phase_desc = "Настрой трекер для персонализированных советов."
    
    # Получаем советы для фазы из БД
    async with db.async_session() as session:
        from sqlalchemy import select
        result = await session.execute(
            select(db.CycleTip).where(db.CycleTip.phase == phase_id)
        )
        tips = result.scalars().all()
    
    text = f"💡 <b>Советы: {phase_name}</b>\n\n{phase_desc}\n\n"
    
    if tips:
        text += "<b>Рекомендации:</b>\n"
        for i, tip in enumerate(tips[:3], 1):
            text += f"{i}. {tip.content}\n"
    else:
        text += "Советы добавляются администратором."
    
    await callback.message.edit_text(text, reply_markup=cycle_main_keyboard())
    await callback.answer()
@router.callback_query(F.data == "cycle_back")
async def cycle_back(callback: CallbackQuery):
    """Назад в цикл"""
    await callback.message.delete()
    await show_cycle(callback.message)
    await callback.answer()

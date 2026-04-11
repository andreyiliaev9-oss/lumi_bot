import io
import csv
from datetime import datetime, date, timedelta
from calendar import monthcalendar

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.filters import StateFilter
from sqlalchemy import select

# ТЕ САМЫЕ ИМПОРТЫ, ИЗ-ЗА КОТОРЫХ БЫЛА ОШИБКА
from db.db import async_session
from db.models import User, CycleLog, CycleTip
from keyboards.inline import back_button

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

# --- Главное меню цикла ---
@router.callback_query(F.data == "cycle")
async def cycle_menu(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        if not user or not user.cycle_start_date:
            text = "🌸 Трекер цикла не настроен.\nУкажите дату начала последних месячных."
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📅 Настроить цикл", callback_data="setup_cycle")],
                [InlineKeyboardButton(text="🔙 Назад", callback_data="exit_private")]
            ])
            await callback.message.edit_text(text, reply_markup=kb)
            await callback.answer()
            return

        today = date.today()
        delta = (today - user.cycle_start_date).days
        cycle_day = (delta % user.cycle_length) + 1
        phase_key = get_phase_key(cycle_day, user.period_length)
        phase_emoji = get_phase_emoji(phase_key)

        tip_record = await session.scalar(
            select(CycleTip).where(CycleTip.phase == phase_key, CycleTip.is_active == True)
        )
        advice = tip_record.tip if tip_record else "Будьте внимательны к своему организму."

        next_period = user.cycle_start_date + timedelta(days=user.cycle_length)
        days_left = (next_period - today).days

        text = (
            f"{phase_emoji} <b>День цикла: {cycle_day}</b>\n"
            f"📌 Фаза: {phase_key.capitalize()}\n"
            f"📅 Следующие месячные: {next_period.strftime('%d.%m.%Y')}\n"
            f"⏳ Осталось дней: {days_left}\n"
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
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

# --- Настройка цикла ---
@router.callback_query(F.data == "setup_cycle")
async def setup_cycle_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите дату начала последних месячных в формате <b>ДД.ММ.ГГГГ</b> (например, 10.04.2026):")
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
    except:
        await message.answer("❌ Неверный формат. Используйте ДД.ММ.ГГГГ")

@router.message(CycleForm.cycle_length)
async def get_cycle_length(message: Message, state: FSMContext):
    try:
        length = int(message.text)
        if length < 21 or length > 45:
            await message.answer("Обычно цикл от 21 до 45 дней. Попробуйте ещё раз.")
            return
        await state.update_data(cycle_length=length)
        await message.answer("Введите длительность месячных (в днях):")
        await state.set_state(CycleForm.period_length)
    except:
        await message.answer("Введите число.")

@router.message(CycleForm.period_length)
async def get_period_length(message: Message, state: FSMContext):
    try:
        period = int(message.text)
        if period < 2 or period > 10:
            await message.answer("Обычно 3-7 дней. Попробуйте ещё раз.")
            return
        data = await state.get_data()
        async with async_session() as session:
            user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
            if user:
                user.cycle_start_date = data['start_date']
                user.cycle_length = data['cycle_length']
                user.period_length = period
                await session.commit()
        await message.answer("✅ Настройки цикла сохранены!")
        await state.clear()
        # Имитируем нажатие кнопки меню для возврата
        await cycle_menu_fake(message)
    except:
        await message.answer("Введите число.")

# Вспомогательная функция для возврата в меню
async def cycle_menu_fake(message: Message):
    class FakeCallback:
        from_user = message.from_user
        message = message
        async def answer(self): pass
    await cycle_menu(FakeCallback(), None)

# --- Логика опроса самочувствия ---
@router.callback_query(F.data == "log_feeling")
async def log_feeling_start(callback: CallbackQuery, state: FSMContext):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"mood_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Оцените настроение (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.mood)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.mood))
async def get_mood(callback: CallbackQuery, state: FSMContext):
    await state.update_data(mood=int(callback.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"pain_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Уровень боли (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.pain)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.pain))
async def get_pain(callback: CallbackQuery, state: FSMContext):
    await state.update_data(pain=int(callback.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"energy_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Уровень энергии (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.energy)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.energy))
async def get_energy(callback: CallbackQuery, state: FSMContext):
    await state.update_data(energy=int(callback.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=str(i), callback_data=f"sleep_{i}") for i in range(1, 6)]
    ])
    await callback.message.edit_text("Качество сна (1-5):", reply_markup=kb)
    await state.set_state(FeelingForm.sleep)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.sleep))
async def get_sleep(callback: CallbackQuery, state: FSMContext):
    await state.update_data(sleep=int(callback.data.split("_")[1]))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤕 Да", callback_data="h_yes"), InlineKeyboardButton(text="✅ Нет", callback_data="h_no")]
    ])
    await callback.message.edit_text("Есть головная боль?", reply_markup=kb)
    await state.set_state(FeelingForm.headache)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.headache))
async def get_headache(callback: CallbackQuery, state: FSMContext):
    await state.update_data(headache=(callback.data == "h_yes"))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤰 Да", callback_data="b_yes"), InlineKeyboardButton(text="✅ Нет", callback_data="b_no")]
    ])
    await callback.message.edit_text("Беспокоит вздутие?", reply_markup=kb)
    await state.set_state(FeelingForm.bloating)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.bloating))
async def get_bloating(callback: CallbackQuery, state: FSMContext):
    await state.update_data(bloating=(callback.data == "b_yes"))
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="😖 Да", callback_data="a_yes"), InlineKeyboardButton(text="✅ Нет", callback_data="a_no")]
    ])
    await callback.message.edit_text("Есть высыпания (акне)?", reply_markup=kb)
    await state.set_state(FeelingForm.acne)
    await callback.answer()

@router.callback_query(StateFilter(FeelingForm.acne))
async def get_acne(callback: CallbackQuery, state: FSMContext):
    await state.update_data(acne=(callback.data == "a_yes"))
    await callback.message.edit_text("Добавьте заметку (или '-' для пропуска):")
    await state.set_state(FeelingForm.notes)
    await callback.answer()

@router.message(FeelingForm.notes)
async def get_notes(message: Message, state: FSMContext):
    notes = None if message.text == "-" else message.text
    data = await state.get_data()
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == message.from_user.id))
        if user:
            log = CycleLog(
                user_id=user.id, date=date.today(),
                mood=data.get('mood'), pain=data.get('pain'),
                energy=data.get('energy'), sleep=data.get('sleep'),
                headache=data.get('headache'), bloating=data.get('bloating'),
                acne=data.get('acne'), notes=notes
            )
            session.add(log)
            await session.commit()
    await message.answer("✅ Самочувствие сохранено!")
    await state.clear()
    await cycle_menu_fake(message)

# --- Статистика ---
@router.callback_query(F.data == "cycle_stats")
async def cycle_stats(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        logs = await session.scalars(select(CycleLog).where(CycleLog.user_id == user.id).order_by(CycleLog.date.desc()).limit(5))
        logs_list = logs.all()
        if not logs_list:
            text = "Данных пока нет."
        else:
            text = "📊 <b>Последние записи:</b>\n"
            for log in logs_list:
                text += f"\n📅 {log.date.strftime('%d.%m')}: Настроение {log.mood}, Боль {log.pain}"
        await callback.message.edit_text(text, reply_markup=back_button("cycle"))
    await callback.answer()

# --- Календарь ---
@router.callback_query(F.data == "cycle_calendar")
async def cycle_calendar(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        today = date.today()
        cal = monthcalendar(today.year, today.month)
        text = f"📅 <b>{today.strftime('%B %Y')}</b>\n\n"
        for week in cal:
            line = ""
            for day in week:
                if day == 0: line += "   "
                else:
                    d = date(today.year, today.month, day)
                    delta = (d - user.cycle_start_date).days
                    c_day = (delta % user.cycle_length) + 1
                    status = "🩸" if c_day <= user.period_length else "•"
                    line += f"{day:2d}{status} "
            text += line + "\n"
        await callback.message.edit_text(text, reply_markup=back_button("cycle"))
    await callback.answer()

# --- Экспорт ---
@router.callback_query(F.data == "export_cycle_data")
async def export_cycle_data(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        logs = await session.scalars(select(CycleLog).where(CycleLog.user_id == user.id))
        logs_list = logs.all()
        if not logs_list:
            await callback.answer("Нет данных")
            return
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["Дата", "Настроение", "Боль"])
        for log in logs_list:
            writer.writerow([log.date, log.mood, log.pain])
        csv_bytes = output.getvalue().encode('utf-8')
        await callback.message.answer_document(BufferedInputFile(csv_bytes, filename="cycle.csv"))
    await callback.answer()

# --- Советы ---
@router.callback_query(F.data == "all_tips")
async def show_all_tips(callback: CallbackQuery):
    async with async_session() as session:
        tips = await session.scalars(select(CycleTip).where(CycleTip.is_active == True))
        tips_list = tips.all()
        text = "💡 <b>Советы:</b>\n\n" + "\n".join([f"• {t.tip}" for t in tips_list]) if tips_list else "Советов нет."
        await callback.message.edit_text(text, reply_markup=back_button("cycle"))
    await callback.answer()

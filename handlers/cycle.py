from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date

from db.db import async_session
from db.models import User, CycleTip
from sqlalchemy import select, update
from keyboards.inline import cycle_main_kb, private_main_menu_kb

router = Router()

class CycleSetup(StatesGroup):
    waiting_for_start_date = State()
    waiting_for_cycle_len = State()
    waiting_for_period_len = State()

# Вспомогательная функция для расчета фазы
def get_cycle_phase(day: int, cycle_len: int, period_len: int):
    if 1 <= day <= period_len:
        return "Менструация 🩸", "menstruation"
    elif day <= (cycle_len - 16):
        return "Фолликулярная фаза 🐣", "follicular"
    elif day <= (cycle_len - 13):
        return "Овуляция ✨", "ovulation"
    else:
        return "Лютеиновая фаза 🌙", "luteal"

@router.callback_query(F.data == "p_cycle")
async def cycle_index(callback: CallbackQuery):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == callback.from_user.id))
        
        if not user.cycle_start_date:
            await callback.message.edit_text(
                "🌸 <b>Трекер цикла</b>\n\nУ вас еще не настроен календарь. Нажмите кнопку ниже, чтобы начать.",
                reply_markup=cycle_main_kb(), parse_mode="HTML"
            )
        else:
            # Математический расчет текущего дня
            today = date.today()
            delta = (today - user.cycle_start_date).days
            current_day = (delta % user.cycle_length) + 1
            
            phase_name, phase_key = get_cycle_phase(current_day, user.cycle_length, user.period_length)
            
            # Получаем совет из базы
            tip = await session.scalar(select(CycleTip).where(CycleTip.phase == phase_key))
            tip_text = tip.text if tip else "Слушай своё тело и не забывай об отдыхе 💜"

            text = (
                f"🌸 <b>ТВОЙ ЦИКЛ</b>\n"
                f"━━━━━━━━━━━━━━\n\n"
                f"📅 Сегодня: <b>{current_day}-й день</b>\n"
                f"🎭 Фаза: <b>{phase_name}</b>\n\n"
                f"💡 <b>Совет ЛЮМИ:</b>\n<i>{tip_text}</i>\n\n"
                f"━━━━━━━━━━━━━━"
            )
            await callback.message.edit_text(text, reply_markup=cycle_main_kb(), parse_mode="HTML")

# --- ПРОЦЕСС НАСТРОЙКИ ---
@router.callback_query(F.data == "cycle_setup")
async def start_setup(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите дату начала последних месячных в формате <b>ДД.ММ.ГГГГ</b> (например, 01.04.2026):", parse_mode="HTML")
    await state.set_state(CycleSetup.waiting_for_start_date)

@router.message(CycleSetup.waiting_for_start_date)
async def process_start_date(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%d.%m.%Y").date()
        await state.update_data(start_date=dt)
        await message.answer("Какова средняя длительность вашего цикла? (обычно 28 дней):")
        await state.set_state(CycleSetup.waiting_for_cycle_len)
    except ValueError:
        await message.answer("❌ Ошибка в формате. Введите дату как ДД.ММ.ГГГГ (например, 10.04.2026):")

@router.message(CycleSetup.waiting_for_cycle_len)
async def process_cycle_len(message: Message, state: FSMContext):
    if message.text.isdigit() and 21 <= int(message.text) <= 45:
        await state.update_data(cycle_len=int(message.text))
        await message.answer("Сколько дней обычно длятся месячные? (например, 5):")
        await state.set_state(CycleSetup.waiting_for_period_len)
    else:
        await message.answer("Пожалуйста, введите число от 21 до 45.")

@router.message(CycleSetup.waiting_for_period_len)
async def process_period_len(message: Message, state: FSMContext):
    if message.text.isdigit() and 2 <= int(message.text) <= 10:
        data = await state.get_data()
        async with async_session() as session:
            await session.execute(update(User).where(User.tg_id == message.from_user.id).values(
                cycle_start_date=data['start_date'],
                cycle_length=data['cycle_len'],
                period_length=int(message.text)
            ))
            await session.commit()
        await state.clear()
        await message.answer("✅ <b>Настройка завершена!</b>\nТеперь я буду рассчитывать ваш цикл автоматически.", reply_markup=private_main_menu_kb(), parse_mode="HTML")
    else:
        await message.answer("Пожалуйста, введите число от 2 до 10.")

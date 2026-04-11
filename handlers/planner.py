from aiogram import Router, F
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from datetime import datetime, date
from sqlalchemy import select
from db.db import async_session
from db.models import Event
from keyboards.inline import back_button

router = Router()

class EventForm(StatesGroup):
    title = State()
    description = State()
    date = State()
    time = State()
    notify = State()

@router.callback_query(F.data == "planner")
async def planner_menu(callback: CallbackQuery):
    await callback.message.edit_text("📅 Планировщик:", reply_markup=InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать событие", callback_data="add_event")],
        [InlineKeyboardButton(text="📋 Мои события", callback_data="list_events")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="start")]
    ]))
    await callback.answer()

@router.callback_query(F.data == "add_event")
async def add_event_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введите название события:")
    await state.set_state(EventForm.title)
    await callback.answer()

@router.message(EventForm.title)
async def event_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Введите описание (или '-' для пропуска)")
    await state.set_state(EventForm.description)

@router.message(EventForm.description)
async def event_desc(message: Message, state: FSMContext):
    desc = message.text if message.text != "-" else ""
    await state.update_data(description=desc)
    await message.answer("Введите дату в формате <b>ДД.ММ.ГГГГ</b> (например, 31.12.2025):")
    await state.set_state(EventForm.date)

@router.message(EventForm.date)
async def event_date(message: Message, state: FSMContext):
    try:
        event_date = datetime.strptime(message.text, "%d.%m.%Y").date()
        if event_date < date.today():
            await message.answer("⚠️ Дата не может быть в прошлом. Введите корректную дату.")
            return
    except:
        await message.answer("❌ Неверный формат. Используйте <b>ДД.ММ.ГГГГ</b>, например 31.12.2025")
        return
    await state.update_data(date=event_date)
    await message.answer("Введите время в формате <b>ЧЧ:ММ</b> (или '-' если без времени):")
    await state.set_state(EventForm.time)

@router.message(EventForm.time)
async def event_time(message: Message, state: FSMContext):
    time_val = None if message.text == "-" else message.text
    if time_val:
        try:
            datetime.strptime(time_val, "%H:%M")
        except:
            await message.answer("❌ Неверный формат времени. Используйте ЧЧ:ММ")
            return
    await state.update_data(time=time_val)
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="24ч", callback_data="24h"), InlineKeyboardButton(text="12ч", callback_data="12h")],
        [InlineKeyboardButton(text="7ч", callback_data="7h"), InlineKeyboardButton(text="5ч", callback_data="5h")],
        [InlineKeyboardButton(text="3ч", callback_data="3h"), InlineKeyboardButton(text="1ч", callback_data="1h")],
        [InlineKeyboardButton(text="🚫 Без уведомления", callback_data="none")]
    ])
    await message.answer("⏰ Когда уведомить о событии?", reply_markup=kb)
    await state.set_state(EventForm.notify)

@router.callback_query(EventForm.notify)
async def event_notify(callback: CallbackQuery, state: FSMContext):
    choice = callback.data
    data = await state.get_data()
    async with async_session() as session:
        event = Event(
            user_id=callback.from_user.id,
            title=data['title'],
            description=data['description'],
            date=data['date'],
            time=data['time'],
            notify_before=None if choice == "none" else choice
        )
        session.add(event)
        await session.commit()
    await callback.message.edit_text("✅ Событие создано!", reply_markup=back_button("planner"))
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "list_events")
async def list_events(callback: CallbackQuery):
    async with async_session() as session:
        events = await session.execute(
            select(Event).where(Event.user_id == callback.from_user.id, Event.date >= date.today())
            .order_by(Event.date, Event.time)
        )
        events_list = events.scalars().all()
        if not events_list:
            text = "📭 Нет предстоящих событий."
            await callback.message.edit_text(text, reply_markup=back_button("planner"))
        else:
            kb = InlineKeyboardMarkup(inline_keyboard=[])
            for ev in events_list:
                date_str = ev.date.strftime("%d.%m.%Y")
                kb.inline_keyboard.append([InlineKeyboardButton(
                    text=f"📌 {ev.title} ({date_str})",
                    callback_data=f"event_{ev.id}"
                )])
            kb.inline_keyboard.append([InlineKeyboardButton(text="🔙 Назад", callback_data="planner")])
            await callback.message.edit_text("Выберите событие для редактирования или удаления:", reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("event_"))
async def manage_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if not event or event.user_id != callback.from_user.id:
            await callback.answer("Событие не найдено")
            return
        date_str = event.date.strftime("%d.%m.%Y")
        text = f"📌 <b>{event.title}</b>\n📝 {event.description or 'Нет описания'}\n📅 {date_str}"
        if event.time:
            text += f" в {event.time}"
        if event.notify_before:
            text += f"\n⏰ Уведомление за {event.notify_before}"
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{event_id}"),
             InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_{event_id}")],
            [InlineKeyboardButton(text="🔙 Назад", callback_data="list_events")]
        ])
        await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()

@router.callback_query(F.data.startswith("delete_"))
async def delete_event(callback: CallbackQuery):
    event_id = int(callback.data.split("_")[1])
    async with async_session() as session:
        event = await session.get(Event, event_id)
        if event and event.user_id == callback.from_user.id:
            await session.delete(event)
            await session.commit()
            await callback.answer("🗑 Событие удалено")
            await list_events(callback)
        else:
            await callback.answer("Ошибка")

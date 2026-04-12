from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import database as db
from keyboards import *
from states import EventStates
from handlers import main_menu_keyboard, cancel_keyboard, clear_user_data
router = Router()
# ============== ПЛАНИРОВЩИК ==============
@router.message(F.text == "📅 Планировщик")
async def show_planner(message: Message):
    """Показать планировщик"""
    user = await db.get_user(message.from_user.id)
    events = await db.get_user_events(user.id)
    
    if not events:
        await message.answer(
            "📅 <b>Планировщик</b>\n\n"
            "У тебя нет предстоящих событий.\n\n"
            "Добавь первое событие:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить событие", callback_data="event_add")]
                ]
            )
        )
        return
    
    await message.answer(
        "📅 <b>Предстоящие события:</b>",
        reply_markup=events_inline_keyboard(events)
    )
@router.callback_query(F.data == "event_add")
async def event_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления события"""
    await state.set_state(EventStates.waiting_title)
    await callback.message.edit_text(
        "➕ <b>Новое событие</b>\n\n"
        "Введи название события:"
    )
    await callback.answer()
    await callback.message.answer(
        "Для отмены отправь /cancel",
        reply_markup=cancel_keyboard()
    )
@router.message(StateFilter(EventStates.waiting_title))
async def event_title_received(message: Message, state: FSMContext):
    """Получено название события"""
    await state.update_data(event_title=message.text)
    await state.set_state(EventStates.waiting_description)
    await message.answer("📝 Введи описание (или 'пропустить'):")
@router.message(StateFilter(EventStates.waiting_description))
async def event_description_received(message: Message, state: FSMContext):
    """Получено описание события"""
    description = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(event_description=description)
    await state.set_state(EventStates.waiting_date)
    await message.answer(
        "📅 Введи дату события (ДД.ММ.ГГГГ):\n\n"
        "Например: 25.12.2024"
    )
@router.message(StateFilter(EventStates.waiting_date))
async def event_date_received(message: Message, state: FSMContext):
    """Получена дата события"""
    try:
        date = datetime.strptime(message.text, "%d.%m.%Y")
        if date < datetime.now().replace(hour=0, minute=0, second=0):
            await message.answer("❌ Дата не может быть в прошлом. Введи другую дату:")
            return
        
        await state.update_data(event_date=date)
        await state.set_state(EventStates.waiting_time)
        await message.answer(
            "⏰ Введи время события (ЧЧ:ММ) или 'пропустить':\n\n"
            "Например: 14:30"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Введи дату как ДД.ММ.ГГГГ:")
@router.message(StateFilter(EventStates.waiting_time))
async def event_time_received(message: Message, state: FSMContext):
    """Получено время события"""
    time_str = None
    if message.text.lower() != "пропустить":
        try:
            datetime.strptime(message.text, "%H:%M")
            time_str = message.text
        except ValueError:
            await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ или 'пропустить':")
            return
    
    await state.update_data(event_time=time_str)
    await state.set_state(EventStates.waiting_notifications)
    await message.answer(
        "🔔 Выбери уведомления (можно несколько):",
        reply_markup=event_notifications_keyboard()
    )
@router.callback_query(F.data.startswith("notif_"), StateFilter(EventStates.waiting_notifications))
async def event_notification_selected(callback: CallbackQuery, state: FSMContext):
    """Выбрано время уведомления"""
    notif_type = callback.data.replace("notif_", "")
    
    if notif_type == "done":
        # Сохраняем событие
        data = await state.get_data()
        user = await db.get_user(callback.from_user.id)
        
        notifications = data.get("selected_notifications", [1])
        
        event = await db.create_event(
            user_id=user.id,
            title=data["event_title"],
            description=data.get("event_description"),
            event_date=data["event_date"],
            event_time=data.get("event_time"),
            notifications=str(notifications)
        )
        
        await state.clear()
        await callback.message.edit_text(
            f"✅ Событие '<b>{event.title}</b>' создано!\n\n"
            f"📅 Дата: {event.event_date.strftime('%d.%m.%Y')}\n"
            f"⏰ Время: {event.event_time or 'Не указано'}\n"
            f"🔔 Уведомления: {', '.join(f'{n}ч' for n in notifications)}"
        )
        await callback.message.answer(
            "Главное меню:",
            reply_markup=main_menu_keyboard()
        )
        
    else:
        # Добавляем/убираем уведомление
        data = await state.get_data()
        selected = data.get("selected_notifications", [])
        hours = int(notif_type)
        
        if hours in selected:
            selected.remove(hours)
        else:
            selected.append(hours)
        
        await state.update_data(selected_notifications=selected)
        await callback.answer(f"Уведомление за {hours}ч {'добавлено' if hours in selected else 'убрано'}")
@router.callback_query(F.data.startswith("event_view_"))
async def event_view(callback: CallbackQuery):
    """Просмотр события"""
    event_id = int(callback.data.replace("event_view_", ""))
    
    async with db.async_session() as session:
        event = await session.get(db.Event, event_id)
        
        if not event:
            await callback.answer("Событие не найдено")
            return
        
        date_str = event.event_date.strftime("%d.%m.%Y")
        time_str = event.event_time or "Не указано"
        status_emoji = {
            "pending": "⏳",
            "completed": "✅",
            "skipped": "❌",
            "postponed": "➡️"
        }.get(event.status, "⏳")
        
        text = (
            f"📅 <b>{event.title}</b>\n\n"
            f"📝 Описание: {event.description or 'Нет'}\n"
            f"📆 Дата: {date_str}\n"
            f"⏰ Время: {time_str}\n"
            f"{status_emoji} Статус: {event.status}\n"
        )
        
        await callback.message.edit_text(text, reply_markup=event_actions_keyboard(event.id))
        await callback.answer()
@router.callback_query(F.data.startswith("event_complete_"))
async def event_complete(callback: CallbackQuery):
    """Отметить событие выполненным"""
    event_id = int(callback.data.replace("event_complete_", ""))
    
    async with db.async_session() as session:
        event = await session.get(db.Event, event_id)
        if event:
            event.status = "completed"
            await session.commit()
            
            # Начисляем XP
            await db.update_user_xp(event.user_id, 15)
    
    await callback.answer("✅ Событие выполнено! +15 XP")
    await callback.message.edit_text("🎉 Событие выполнено! Отличная работа!")
@router.callback_query(F.data.startswith("event_skip_"))
async def event_skip(callback: CallbackQuery):
    """Пропустить событие"""
    event_id = int(callback.data.replace("event_skip_", ""))
    
    async with db.async_session() as session:
        event = await session.get(db.Event, event_id)
        if event:
            event.status = "skipped"
            await session.commit()
    
    await callback.answer("Событие пропущено")
    await callback.message.edit_text("⏭ Событие отмечено как пропущенное.")
@router.callback_query(F.data.startswith("event_postpone_"))
async def event_postpone_start(callback: CallbackQuery, state: FSMContext):
    """Начало переноса события"""
    event_id = int(callback.data.replace("event_postpone_", ""))
    await state.set_state(EventStates.waiting_postpone_date)
    await state.update_data(postpone_event_id=event_id)
    
    await callback.message.edit_text(
        "📅 Введи новую дату (ДД.ММ.ГГГГ):\n\n"
        "Событие будет перенесено."
    )
    await callback.answer()
@router.message(StateFilter(EventStates.waiting_postpone_date))
async def event_postpone_date_received(message: Message, state: FSMContext):
    """Получена новая дата для переноса"""
    try:
        new_date = datetime.strptime(message.text, "%d.%m.%Y")
        data = await state.get_data()
        event_id = data["postpone_event_id"]
        
        async with db.async_session() as session:
            event = await session.get(db.Event, event_id)
            if event:
                event.event_date = new_date
                event.status = "postponed"
                await session.commit()
        
        await state.clear()
        await message.answer(
            f"✅ Событие перенесено на {new_date.strftime('%d.%m.%Y')}",
            reply_markup=main_menu_keyboard()
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат. Введи дату как ДД.ММ.ГГГГ:")
@router.callback_query(F.data.startswith("event_delete_"))
async def event_delete(callback: CallbackQuery):
    """Удалить событие"""
    event_id = int(callback.data.replace("event_delete_", ""))
    
    async with db.async_session() as session:
        event = await session.get(db.Event, event_id)
        if event:
            await session.delete(event)
            await session.commit()
    
    await callback.answer("Событие удалено")
    await callback.message.edit_text("🗑 Событие удалено.")
@router.callback_query(F.data.startswith("event_edit_"))
async def event_edit(callback: CallbackQuery):
    """Редактировать событие"""
    await callback.answer("Редактирование в разработке")

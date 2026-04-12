import random
from datetime import datetime, time as dt_time
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from apscheduler.triggers.cron import CronTrigger
import database as db
from config import settings
from keyboards import *
from states import AdminStates
from handlers import main_menu_keyboard
router = Router()
def is_admin(telegram_id: int) -> bool:
    """Проверка администратора"""
    return telegram_id == settings.ADMIN_ID
# ============== АДМИН ПАНЕЛЬ ==============
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Вход в админ панель"""
    if not is_admin(message.from_user.id):
        await message.answer("⛔ У тебя нет доступа к этой команде.")
        return
    
    await message.answer(
        "🔧 <b>Админ панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )
@router.callback_query(F.data == "admin_back")
async def admin_back(callback: CallbackQuery):
    """Назад в админ панель"""
    await callback.message.edit_text(
        "🔧 <b>Админ панель</b>\n\n"
        "Выбери действие:",
        reply_markup=admin_keyboard()
    )
    await callback.answer()
# ============== РАССЫЛКА ==============
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_start(callback: CallbackQuery, state: FSMContext):
    """Начало рассылки"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    await state.set_state(AdminStates.waiting_broadcast)
    await callback.message.edit_text(
        "📨 <b>Рассылка</b>\n\n"
        "Введи текст сообщения для всех пользователей:\n\n"
        "Или отправь /cancel для отмены"
    )
    await callback.answer()
@router.message(StateFilter(AdminStates.waiting_broadcast))
async def admin_broadcast_send(message: Message, state: FSMContext, bot: Bot):
    """Отправка рассылки"""
    broadcast_text = message.text
    users = await db.get_all_users()
    
    sent = 0
    failed = 0
    
    await message.answer(f"📤 Начинаю рассылку для {len(users)} пользователей...")
    
    for user in users:
        try:
            await bot.send_message(
                user.telegram_id,
                f"📢 <b>Сообщение от ЛЮМИ:</b>\n\n{broadcast_text}"
            )
            sent += 1
        except Exception:
            failed += 1
    
    await state.clear()
    await message.answer(
        f"✅ Рассылка завершена!\n\n"
        f"📤 Отправлено: {sent}\n"
        f"❌ Ошибок: {failed}",
        reply_markup=admin_keyboard()
    )
# ============== УТРЕННИЕ СООБЩЕНИЯ ==============
@router.callback_query(F.data == "admin_morning")
async def admin_morning(callback: CallbackQuery):
    """Управление утренними сообщениями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    await callback.message.edit_text(
        "☀️ <b>Утренние сообщения</b>\n\n"
        "Эти сообщения отправляются всем пользователям по утрам.",
        reply_markup=admin_morning_night_keyboard("morning")
    )
    await callback.answer()
@router.callback_query(F.data == "admin_morning_add")
async def admin_morning_add_start(callback: CallbackQuery, state: FSMContext):
    """Добавление утреннего сообщения"""
    await state.set_state(AdminStates.waiting_morning_time)
    await callback.message.edit_text(
        "☀️ <b>Новое утреннее сообщение</b>\n\n"
        "Введи время отправки (ЧЧ:ММ):\n\n"
        "Например: 08:00"
    )
    await callback.answer()
@router.message(StateFilter(AdminStates.waiting_morning_time))
async def admin_morning_time(message: Message, state: FSMContext):
    """Получено время утреннего сообщения"""
    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(morning_time=message.text)
        await state.set_state(AdminStates.waiting_morning_content)
        await message.answer("Теперь введи текст сообщения:")
    except ValueError:
        await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ:")
@router.message(StateFilter(AdminStates.waiting_morning_content))
async def admin_morning_content(message: Message, state: FSMContext):
    """Получен текст утреннего сообщения"""
    data = await state.get_data()
    
    await db.add_admin_message(
        message_type="morning",
        content=message.text,
        scheduled_time=data["morning_time"]
    )
    
    await state.clear()
    await message.answer(
        "✅ Утреннее сообщение добавлено!",
        reply_markup=admin_keyboard()
    )
@router.callback_query(F.data == "admin_morning_list")
async def admin_morning_list(callback: CallbackQuery):
    """Список утренних сообщений"""
    messages = await db.get_admin_messages("morning")
    
    if not messages:
        await callback.answer("Нет сообщений")
        await callback.message.edit_text(
            "☀️ Утренних сообщений пока нет.",
            reply_markup=admin_morning_night_keyboard("morning")
        )
        return
    
    text = "☀️ <b>Утренние сообщения:</b>\n\n"
    for msg in messages:
        status = "✅" if msg.is_active else "❌"
        text += f"{status} {msg.scheduled_time}: {msg.content[:50]}...\n"
    
    await callback.message.edit_text(text, reply_markup=admin_morning_night_keyboard("morning"))
    await callback.answer()
# ============== НОЧНЫЕ СООБЩЕНИЯ ==============
@router.callback_query(F.data == "admin_night")
async def admin_night(callback: CallbackQuery):
    """Управление ночными сообщениями"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    await callback.message.edit_text(
        "🌙 <b>Ночные сообщения</b>\n\n"
        "Эти сообщения отправляются всем пользователям перед сном.",
        reply_markup=admin_morning_night_keyboard("night")
    )
    await callback.answer()
@router.callback_query(F.data == "admin_night_add")
async def admin_night_add_start(callback: CallbackQuery, state: FSMContext):
    """Добавление ночного сообщения"""
    await state.set_state(AdminStates.waiting_night_time)
    await callback.message.edit_text(
        "🌙 <b>Новое ночное сообщение</b>\n\n"
        "Введи время отправки (ЧЧ:ММ):\n\n"
        "Например: 22:00"
    )
    await callback.answer()
@router.message(StateFilter(AdminStates.waiting_night_time))
async def admin_night_time(message: Message, state: FSMContext):
    """Получено время ночного сообщения"""
    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(night_time=message.text)
        await state.set_state(AdminStates.waiting_night_content)
        await message.answer("Теперь введи текст сообщения:")
    except ValueError:
        await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ:")
@router.message(StateFilter(AdminStates.waiting_night_content))
async def admin_night_content(message: Message, state: FSMContext):
    """Получен текст ночного сообщения"""
    data = await state.get_data()
    
    await db.add_admin_message(
        message_type="night",
        content=message.text,
        scheduled_time=data["night_time"]
    )
    
    await state.clear()
    await message.answer(
        "✅ Ночное сообщение добавлено!",
        reply_markup=admin_keyboard()
    )
@router.callback_query(F.data == "admin_night_list")
async def admin_night_list(callback: CallbackQuery):
    """Список ночных сообщений"""
    messages = await db.get_admin_messages("night")
    
    if not messages:
        await callback.answer("Нет сообщений")
        await callback.message.edit_text(
            "🌙 Ночных сообщений пока нет.",
            reply_markup=admin_morning_night_keyboard("night")
        )
        return
    
    text = "🌙 <b>Ночные сообщения:</b>\n\n"
    for msg in messages:
        status = "✅" if msg.is_active else "❌"
        text += f"{status} {msg.scheduled_time}: {msg.content[:50]}...\n"
    
    await callback.message.edit_text(text, reply_markup=admin_morning_night_keyboard("night"))
    await callback.answer()
# ============== СОВЕТЫ ЦИКЛА ==============
@router.callback_query(F.data == "admin_tips")
async def admin_tips(callback: CallbackQuery, state: FSMContext):
    """Добавление советов для цикла"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    await state.set_state(AdminStates.waiting_tip_phase)
    await callback.message.edit_text(
        "💡 <b>Советы для цикла</b>\n\n"
        "Выбери фазу:\n"
        "1 - Менструация\n"
        "2 - Фолликулярная\n"
        "3 - Овуляция\n"
        "4 - Лютеиновая\n\n"
        "Введи номер фазы:"
    )
    await callback.answer()
@router.message(StateFilter(AdminStates.waiting_tip_phase))
async def admin_tip_phase(message: Message, state: FSMContext):
    """Выбрана фаза для совета"""
    phases = {
        "1": "menstruation",
        "2": "follicular",
        "3": "ovulation",
        "4": "luteal"
    }
    
    if message.text not in phases:
        await message.answer("Введи число от 1 до 4:")
        return
    
    await state.update_data(tip_phase=phases[message.text])
    await state.set_state(AdminStates.waiting_tip_content)
    await message.answer("Введи текст совета:")
@router.message(StateFilter(AdminStates.waiting_tip_content))
async def admin_tip_content(message: Message, state: FSMContext):
    """Получен текст совета"""
    data = await state.get_data()
    
    await db.add_cycle_tip(
        phase=data["tip_phase"],
        content=message.text
    )
    
    await state.clear()
    await message.answer(
        "✅ Совет добавлен!",
        reply_markup=admin_keyboard()
    )
# ============== ПОЛЬЗОВАТЕЛИ ==============
@router.callback_query(F.data == "admin_users")
async def admin_users(callback: CallbackQuery):
    """Список пользователей"""
    if not is_admin(callback.from_user.id):
        await callback.answer("Нет доступа")
        return
    
    users = await db.get_all_users()
    
    text = f"👥 <b>Пользователи ({len(users)}):</b>\n\n"
    
    for user in users[:20]:  # Первые 20
        name = user.first_name or user.username or f"ID:{user.telegram_id}"
        text += f"• {name} - Уровень {user.level}\n"
    
    if len(users) > 20:
        text += f"\n...и ещё {len(users) - 20} пользователей"
    
    await callback.message.edit_text(text, reply_markup=admin_keyboard())
    await callback.answer()
# ============== ФУНКЦИИ ДЛЯ ПЛАНИРОВЩИКА ЗАДАЧ ==============
async def send_morning_messages(bot: Bot):
    """Отправка утренних сообщений"""
    messages = await db.get_admin_messages("morning")
    if not messages:
        return
    
    message = random.choice(messages)
    users = await db.get_all_users()
    
    for user in users:
        if not user.notifications_enabled or not user.morning_night_notifications:
            continue
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"☀️ <b>Доброе утро!</b>\n\n{message.content}\n\nХорошего дня! 💚"
            )
        except Exception:
            pass
async def send_night_messages(bot: Bot):
    """Отправка ночных сообщений"""
    messages = await db.get_admin_messages("night")
    if not messages:
        return
    
    message = random.choice(messages)
    users = await db.get_all_users()
    
    for user in users:
        if not user.notifications_enabled or not user.morning_night_notifications:
            continue
        
        try:
            await bot.send_message(
                user.telegram_id,
                f"🌙 <b>Доброй ночи!</b>\n\n{message.content}\n\nСпокойной ночи! 🌟"
            )
        except Exception:
            pass
def setup_schedulers(scheduler, bot: Bot):
    """Настройка планировщика задач"""
    # Утренние сообщения (08:00 по умолчанию)
    scheduler.add_job(
        send_morning_messages,
        CronTrigger(hour=8, minute=0),
        args=[bot],
        id="morning_messages",
        replace_existing=True
    )
    
    # Ночные сообщения (22:00 по умолчанию)
    scheduler.add_job(
        send_night_messages,
        CronTrigger(hour=22, minute=0),
        args=[bot],
        id="night_messages",
        replace_existing=True
    )

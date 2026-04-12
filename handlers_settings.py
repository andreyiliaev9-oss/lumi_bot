from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
import database as db
from keyboards import *
from states import SettingsStates
from handlers import main_menu_keyboard
router = Router()
# ============== НАСТРОЙКИ ==============
@router.message(F.text == "⚙️ Настройки")
async def show_settings(message: Message):
    """Показать настройки"""
    user = await db.get_user(message.from_user.id)
    
    quiet_mode = "🌙 Тихий режим: "
    if user.quiet_mode_start and user.quiet_mode_end:
        quiet_mode += f"{user.quiet_mode_start}-{user.quiet_mode_end}"
    else:
        quiet_mode += "выключен"
    
    await message.answer(
        f"⚙️ <b>Настройки</b>\n\n"
        f"{quiet_mode}\n\n"
        f"🔔 Уведомления: {'включены' if user.notifications_enabled else 'выключены'}\n\n"
        f"Выбери, что хочешь настроить:",
        reply_markup=settings_keyboard()
    )
@router.callback_query(F.data == "settings_notifications")
async def settings_notifications(callback: CallbackQuery):
    """Настройки уведомлений"""
    user = await db.get_user(callback.from_user.id)
    
    await callback.message.edit_text(
        "🔔 <b>Настройки уведомлений</b>\n\n"
        "Нажми на категорию, чтобы включить/выключить:",
        reply_markup=notifications_settings_keyboard(user)
    )
    await callback.answer()
@router.callback_query(F.data.startswith("notif_toggle_"))
async def toggle_notification(callback: CallbackQuery):
    """Переключение уведомлений"""
    toggle_type = callback.data.replace("notif_toggle_", "")
    user = await db.get_user(callback.from_user.id)
    
    async with db.async_session() as session:
        if toggle_type == "habits":
            user.habit_notifications = not user.habit_notifications
        elif toggle_type == "planner":
            user.planner_notifications = not user.planner_notifications
        elif toggle_type == "cycle":
            user.cycle_notifications = not user.cycle_notifications
        elif toggle_type == "morning":
            user.morning_night_notifications = not user.morning_night_notifications
        elif toggle_type == "global":
            user.notifications_enabled = not user.notifications_enabled
        
        await session.merge(user)
        await session.commit()
    
    # Обновляем клавиатуру
    await callback.message.edit_reply_markup(
        reply_markup=notifications_settings_keyboard(user)
    )
    await callback.answer()
@router.callback_query(F.data == "settings_quiet")
async def settings_quiet(callback: CallbackQuery):
    """Настройка тихого режима"""
    user = await db.get_user(callback.from_user.id)
    
    text = "🌙 <b>Тихий режим</b>\n\n"
    
    if user.quiet_mode_start and user.quiet_mode_end:
        text += f"Сейчас установлено: {user.quiet_mode_start} - {user.quiet_mode_end}\n\n"
    else:
        text += "Сейчас тихий режим отключен.\n\n"
    
    text += "В это время не будут приходить уведомления."
    
    await callback.message.edit_text(text, reply_markup=quiet_mode_keyboard())
    await callback.answer()
@router.callback_query(F.data == "quiet_start")
async def quiet_start_set(callback: CallbackQuery, state: FSMContext):
    """Установка времени начала тихого режима"""
    await state.set_state(SettingsStates.waiting_quiet_start)
    await callback.message.edit_text(
        "🌙 <b>Начало тихого режима</b>\n\n"
        "Введи время в формате ЧЧ:ММ\n\n"
        "Например: 22:00"
    )
    await callback.answer()
@router.message(StateFilter(SettingsStates.waiting_quiet_start))
async def quiet_start_received(message: Message, state: FSMContext):
    """Получено время начала тихого режима"""
    try:
        datetime.strptime(message.text, "%H:%M")
        await state.update_data(quiet_start=message.text)
        await state.set_state(SettingsStates.waiting_quiet_end)
        await message.answer(
            "☀️ <b>Конец тихого режима</b>\n\n"
            "Введи время в формате ЧЧ:ММ\n\n"
            "Например: 09:00"
        )
    except ValueError:
        await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ:")
@router.message(StateFilter(SettingsStates.waiting_quiet_end))
async def quiet_end_received(message: Message, state: FSMContext):
    """Получено время окончания тихого режима"""
    try:
        datetime.strptime(message.text, "%H:%M")
        data = await state.get_data()
        user = await db.get_user(message.from_user.id)
        
        async with db.async_session() as session:
            user.quiet_mode_start = data["quiet_start"]
            user.quiet_mode_end = message.text
            await session.merge(user)
            await session.commit()
        
        await state.clear()
        await message.answer(
            f"✅ Тихий режим установлен!\n\n"
            f"🌙 {data['quiet_start']} - {message.text}\n\n"
            f"В это время уведомления не будут приходить.",
            reply_markup=main_menu_keyboard()
        )
        
    except ValueError:
        await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ:")
@router.callback_query(F.data == "quiet_disable")
async def quiet_disable(callback: CallbackQuery):
    """Отключение тихого режима"""
    user = await db.get_user(callback.from_user.id)
    
    async with db.async_session() as session:
        user.quiet_mode_start = None
        user.quiet_mode_end = None
        await session.merge(user)
        await session.commit()
    
    await callback.message.edit_text(
        "✅ Тихий режим отключен.\n\n"
        "Уведомления будут приходить в любое время.",
        reply_markup=settings_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data == "quiet_save")
async def quiet_save(callback: CallbackQuery):
    """Сохранение настроек тихого режима"""
    await callback.message.edit_text(
        "✅ Настройки сохранены!",
        reply_markup=settings_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data == "settings_back")
async def settings_back(callback: CallbackQuery):
    """Назад в настройки"""
    await callback.message.edit_text(
        "⚙️ <b>Настройки</b>\n\n"
        "Выбери, что хочешь настроить:",
        reply_markup=settings_keyboard()
    )
    await callback.answer()
@router.callback_query(F.data == "settings_export")
async def settings_export(callback: CallbackQuery):
    """Экспорт данных"""
    await callback.answer("Экспорт в разработке")
@router.callback_query(F.data == "settings_help")
async def settings_help(callback: CallbackQuery):
    """Помощь"""
    help_text = (
        "❓ <b>Помощь</b>\n\n"
        "<b>ЛЮМИ</b> - твой персональный помощник.\n\n"
        "<b>Основные функции:</b>\n"
        "• <b>Профиль</b> - твоя статистика и уровень\n"
        "• <b>Привычки</b> - отслеживание привычек\n"
        "• <b>Планировщик</b> - события и напоминания\n"
        "• <b>Личное</b> - приватные записи с PIN\n"
        "• <b>Цикл</b> - трекер женского цикла\n"
        "• <b>Настройки</b> - уведомления и тихий режим\n\n"
        "<b>Система уровней:</b>\n"
        "За активность ты получаешь XP.\n"
        "Набирай XP для повышения уровня!\n\n"
        "<b>Команды:</b>\n"
        "/start - Главное меню\n"
        "/help - Эта помощь\n\n"
        "По вопросам обращайся к администратору."
    )
    
    await callback.message.edit_text(help_text)
    await callback.answer()

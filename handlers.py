import asyncio
import json
import random
from datetime import datetime, timedelta
from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramAPIError
import database as db
from config import settings, XP_CONFIG, LEVEL_THRESHOLDS
from keyboards import *
from states import *
router = Router()
# Временное хранилище данных FSM (для PIN и других временных данных)
temp_storage = {}
# ============== UTILS ==============
def get_user_data(user_id: int) -> dict:
    """Получить временные данные пользователя"""
    if user_id not in temp_storage:
        temp_storage[user_id] = {}
    return temp_storage[user_id]
def clear_user_data(user_id: int):
    """Очистить временные данные пользователя"""
    if user_id in temp_storage:
        temp_storage[user_id] = {}
def is_in_quiet_mode(user, current_time: datetime = None) -> bool:
    """Проверка тихого режима"""
    if not user.quiet_mode_start or not user.quiet_mode_end:
        return False
    
    if current_time is None:
        current_time = datetime.utcnow()
    
    current_hour = current_time.hour
    current_minute = current_time.minute
    current_val = current_hour * 60 + current_minute
    
    start_parts = user.quiet_mode_start.split(":")
    end_parts = user.quiet_mode_end.split(":")
    
    start_val = int(start_parts[0]) * 60 + int(start_parts[1])
    end_val = int(end_parts[0]) * 60 + int(end_parts[1])
    
    if start_val <= end_val:
        return start_val <= current_val <= end_val
    else:
        # Например, 22:00 - 09:00
        return current_val >= start_val or current_val <= end_val
# ============== START & MAIN MENU ==============
@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Обработка команды /start"""
    user = await db.get_user(message.from_user.id)
    
    if user:
        # Существующий пользователь
        await message.answer(
            f"👋 С возвращением, {user.first_name or 'друг'}!\n\n"
            f"✨ Твой уровень: {user.level}\n"
            f"⭐ XP: {user.xp}\n"
            f"🔥 Серия: {user.streak} дней\n\n"
            f"Выбери раздел в меню ниже:",
            reply_markup=main_menu_keyboard()
        )
    else:
        # Новый пользователь - онбординг
        await state.set_state(CommonStates.onboarding)
        await message.answer(
            "🌟 Добро пожаловать в ЛЮМИ!\n\n"
            "Я твой персональный помощник для:\n"
            "• Отслеживания привычек\n"
            "• Планирования событий\n"
            "• Управления циклом\n"
            "• Ведения личных записей\n\n"
            "Давай начнём! Нажми кнопку ниже:",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[[KeyboardButton(text="🚀 Начать")]],
                resize_keyboard=True
            )
        )
@router.message(F.text == "🚀 Начать", StateFilter(CommonStates.onboarding))
async def onboarding_complete(message: Message, state: FSMContext):
    """Завершение онбординга"""
    user = await db.create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    await state.clear()
    await message.answer(
        "🎉 Отлично! Твой профиль создан.\n\n"
        "Я начислил тебе бонусные 50 XP за регистрацию!\n\n"
        "Выбери раздел в меню ниже:",
        reply_markup=main_menu_keyboard()
    )
    await db.update_user_xp(user.id, 50)
@router.message(F.text.in_(["◀️ Назад", "❌ Отмена"]))
async def cmd_back(message: Message, state: FSMContext):
    """Возврат в главное меню"""
    await state.clear()
    clear_user_data(message.from_user.id)
    await message.answer(
        "Главное меню:",
        reply_markup=main_menu_keyboard()
    )
# ============== ПРОФИЛЬ ==============
@router.message(F.text == "👤 Профиль")
async def show_profile(message: Message):
    """Показать профиль"""
    user = await db.get_user(message.from_user.id)
    
    if not user:
        await message.answer("Ошибка: пользователь не найден. Нажмите /start")
        return
    
    next_level_xp = LEVEL_THRESHOLDS.get(user.level + 1, user.xp + 1000)
    xp_needed = next_level_xp - user.xp
    
    profile_text = (
        f"👤 <b>Профиль</b>\n\n"
        f"Имя: {user.first_name or 'Не указано'}\n"
        f"Username: @{user.username or 'Нет'}\n"
        f"Дата регистрации: {user.registered_at.strftime('%d.%m.%Y')}\n\n"
        f"🏆 <b>Статистика</b>\n"
        f"Уровень: {user.level}\n"
        f"XP: {user.xp} (до след. уровня: {xp_needed})\n"
        f"🔥 Серия дней: {user.streak}\n\n"
        f"📊 <b>Достижения</b>\n"
        f"Выполнено привычек: {sum(h.total_completions for h in user.habits)}\n"
        f"Записей дневника: {len(user.diary_entries)}\n"
    )
    
    await message.answer(profile_text, reply_markup=profile_inline_keyboard())
@router.callback_query(F.data == "profile_stats")
async def profile_stats(callback: CallbackQuery):
    """Детальная статистика профиля"""
    user = await db.get_user(callback.from_user.id)
    
    stats_text = (
        f"📊 <b>Детальная статистика</b>\n\n"
        f"<b>Привычки:</b>\n"
        f"Активных: {len([h for h in user.habits if h.is_active])}\n"
        f"Всего выполнено: {sum(h.total_completions for h in user.habits)}\n"
        f"Лучшая серия: {max((h.best_streak for h in user.habits), default=0)}\n\n"
        f"<b>События:</b>\n"
        f"Предстоящих: {len([e for e in user.events if e.status == 'pending'])}\n"
        f"Выполнено: {len([e for e in user.events if e.status == 'completed'])}\n\n"
        f"<b>Цикл:</b>\n"
        f"Записей самочувствия: {len(user.cycle_logs)}\n"
    )
    
    await callback.message.edit_text(stats_text)
    await callback.answer()
@router.callback_query(F.data == "profile_diary")
async def profile_diary(callback: CallbackQuery, state: FSMContext):
    """Дневник пользователя"""
    await state.set_state(PrivateStates.waiting_entry_content)
    temp_storage[callback.from_user.id]["diary_mode"] = True
    
    await callback.message.edit_text(
        "📖 <b>Дневник</b>\n\n"
        "Напиши текст для новой записи или отправь /cancel для отмены:"
    )
    await callback.answer()
@router.callback_query(F.data == "profile_achievements")
async def profile_achievements(callback: CallbackQuery):
    """Достижения"""
    user = await db.get_user(callback.from_user.id)
    
    achievements = []
    if user.level >= 5:
        achievements.append("🥉 Мастер привычек (5 уровень)")
    if user.level >= 10:
        achievements.append("🥈 Профи (10 уровень)")
    if user.streak >= 7:
        achievements.append("🔥 Недельная серия")
    if user.streak >= 30:
        achievements.append("🌟 Месячная серия")
    if any(h.best_streak >= 30 for h in user.habits):
        achievements.append("💪 Мастер дисциплины")
    
    if not achievements:
        achievements.append("Пока нет достижений. Продолжай в том же духе!")
    
    text = "🏆 <b>Достижения</b>\n\n" + "\n".join(f"• {a}" for a in achievements)
    
    await callback.message.edit_text(text)
    await callback.answer()
# ============== ПРИВЫЧКИ ==============
@router.message(F.text == "✅ Привычки")
async def show_habits(message: Message):
    """Показать список привычек"""
    user = await db.get_user(message.from_user.id)
    habits = await db.get_user_habits(user.id)
    
    if not habits:
        await message.answer(
            "У тебя пока нет привычек.\n\n"
            "Добавь первую привычку, нажав кнопку ниже:",
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [InlineKeyboardButton(text="➕ Добавить привычку", callback_data="habit_add")]
                ]
            )
        )
        return
    
    await message.answer(
        "📋 <b>Твои привычки:</b>\n\n"
        "Нажми ✅ для отметки выполнения или 📝 для редактирования",
        reply_markup=habits_inline_keyboard(habits)
    )
@router.callback_query(F.data == "habit_add")
async def habit_add_start(callback: CallbackQuery, state: FSMContext):
    """Начало добавления привычки"""
    await state.set_state(HabitStates.waiting_name)
    await callback.message.edit_text(
        "➕ <b>Новая привычка</b>\n\n"
        "Введи название привычки:",
        reply_markup=None
    )
    await callback.answer()
    
    # Отправляем сообщение с клавиатурой отмены
    await callback.message.answer(
        "Для отмены отправь /cancel",
        reply_markup=cancel_keyboard()
    )
@router.message(StateFilter(HabitStates.waiting_name))
async def habit_name_received(message: Message, state: FSMContext):
    """Получено название привычки"""
    await state.update_data(habit_name=message.text)
    await state.set_state(HabitStates.waiting_description)
    await message.answer(
        "📝 Теперь введи описание привычки (или отправь 'пропустить'):"
    )
@router.message(StateFilter(HabitStates.waiting_description))
async def habit_description_received(message: Message, state: FSMContext):
    """Получено описание привычки"""
    description = None if message.text.lower() == "пропустить" else message.text
    await state.update_data(habit_description=description)
    
    await state.set_state(HabitStates.waiting_reminder_time)
    await message.answer(
        "⏰ Укажи время напоминания (ЧЧ:ММ, например 09:00) или 'нет':",
        reply_markup=habit_reminder_keyboard()
    )
@router.callback_query(F.data.startswith("habit_reminder_"), StateFilter(HabitStates.waiting_reminder_time))
async def habit_reminder_type_selected(callback: CallbackQuery, state: FSMContext):
    """Выбран тип напоминания"""
    reminder_type = callback.data.replace("habit_reminder_", "")
    
    if reminder_type == "none":
        # Без напоминаний
        data = await state.get_data()
        user = await db.get_user(callback.from_user.id)
        
        habit = await db.create_habit(
            user_id=user.id,
            name=data["habit_name"],
            description=data.get("habit_description")
        )
        
        await state.clear()
        await callback.message.edit_text(
            f"✅ Привычка '<b>{habit.name}</b>' создана!\n\n"
            "Напоминания отключены."
        )
        await callback.message.answer(
            "Главное меню:",
            reply_markup=main_menu_keyboard()
        )
        
    elif reminder_type == "daily":
        # Ежедневно
        await state.update_data(reminder_days="[1,2,3,4,5,6,7]")
        await callback.message.edit_text("Введи время напоминания (ЧЧ:ММ):")
        
    elif reminder_type == "days":
        # По дням недели
        await callback.message.edit_text(
            "Выбери дни недели:",
            reply_markup=days_of_week_keyboard()
        )
        
    elif reminder_type == "hourly":
        # Каждый час (с ограничением)
        await state.update_data(reminder_interval=60, max_reminders=3)
        await callback.message.edit_text("Введи время первого напоминания (ЧЧ:ММ):")
    
    await callback.answer()
@router.callback_query(F.data.startswith("day_"), StateFilter(HabitStates.waiting_reminder_time))
async def day_selected(callback: CallbackQuery, state: FSMContext):
    """Выбран день недели"""
    day = int(callback.data.replace("day_", ""))
    data = await state.get_data()
    
    selected_days = data.get("selected_days", [])
    if day in selected_days:
        selected_days.remove(day)
    else:
        selected_days.append(day)
    
    await state.update_data(selected_days=selected_days)
    
    # Обновляем клавиатуру (визуальная индикация выбранных дней)
    await callback.answer(f"День {day} {'добавлен' if day in selected_days else 'убран'}")
@router.callback_query(F.data == "days_done", StateFilter(HabitStates.waiting_reminder_time))
async def days_selection_done(callback: CallbackQuery, state: FSMContext):
    """Завершение выбора дней"""
    data = await state.get_data()
    selected_days = data.get("selected_days", [1, 2, 3, 4, 5])
    
    await state.update_data(reminder_days=json.dumps(selected_days))
    await callback.message.edit_text("Введи время напоминания (ЧЧ:ММ):")
    await callback.answer()
@router.message(StateFilter(HabitStates.waiting_reminder_time))
async def habit_time_received(message: Message, state: FSMContext):
    """Получено время напоминания"""
    time_str = message.text
    
    # Простая валидация времени
    try:
        hour, minute = map(int, time_str.split(":"))
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise ValueError
    except ValueError:
        await message.answer("❌ Неверный формат. Введи время как ЧЧ:ММ (например 09:00):")
        return
    
    data = await state.get_data()
    user = await db.get_user(message.from_user.id)
    
    habit = await db.create_habit(
        user_id=user.id,
        name=data["habit_name"],
        description=data.get("habit_description"),
        reminder_time=time_str,
        reminder_days=data.get("reminder_days")
    )
    
    await state.clear()
    await message.answer(
        f"✅ Привычка '<b>{habit.name}</b>' создана!\n\n"
        f"⏰ Напоминание: {time_str}",
        reply_markup=main_menu_keyboard()
    )
@router.callback_query(F.data.startswith("habit_complete_"))
async def habit_complete(callback: CallbackQuery):
    """Отметить привычку выполненной"""
    habit_id = int(callback.data.replace("habit_complete_", ""))
    
    await db.complete_habit(habit_id)
    
    await callback.answer("✅ Привычка выполнена! +10 XP")
    await callback.message.edit_text(
        "🎉 Отлично! Привычка выполнена!\n\n"
        "Продолжай в том же духе! 💪"
    )
@router.callback_query(F.data.startswith("habit_skip_"))
async def habit_skip(callback: CallbackQuery):
    """Пропустить привычку"""
    habit_id = int(callback.data.replace("habit_skip_", ""))
    
    # Логика пропуска (можно добавить статистику пропусков)
    await callback.answer("Привычка пропущена")
    await callback.message.edit_text("⏭ Привычка пропущена. Не сдавайся!")
@router.callback_query(F.data.startswith("habit_disable_"))
async def habit_disable_today(callback: CallbackQuery):
    """Отключить напоминания на сегодня"""
    await callback.answer("🔕 Напоминания отключены на сегодня")
    await callback.message.edit_text(
        "🔕 Напоминания отключены до завтра.\n\n"
        "Отдохни и возвращайся завтра! 🌙"
    )
@router.callback_query(F.data.startswith("habit_delete_"))
async def habit_delete(callback: CallbackQuery):
    """Удалить привычку"""
    habit_id = int(callback.data.replace("habit_delete_", ""))
    
    # Удаление привычки
    async with db.async_session() as session:
        habit = await session.get(db.Habit, habit_id)
        if habit:
            await session.delete(habit)
            await session.commit()
    
    await callback.answer("Привычка удалена")
    await callback.message.edit_text("🗑 Привычка удалена.")
@router.callback_query(F.data == "habits_stats")
async def habits_stats(callback: CallbackQuery):
    """Статистика привычек"""
    user = await db.get_user(callback.from_user.id)
    habits = user.habits
    
    if not habits:
        await callback.answer("У тебя нет привычек")
        return
    
    stats_text = "📊 <b>Статистика привычек:</b>\n\n"
    for habit in habits:
        stats_text += (
            f"• <b>{habit.name}</b>\n"
            f"  Выполнено: {habit.total_completions}\n"
            f"  Текущая серия: {habit.current_streak}\n"
            f"  Лучшая серия: {habit.best_streak}\n\n"
        )
    
    await callback.message.edit_text(stats_text)
    await callback.answer()

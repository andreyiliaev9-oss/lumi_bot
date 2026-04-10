from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, date, timedelta
from aiogram import Bot
from sqlalchemy import select
from db.db import async_session
from db.models import User, Habit, Event

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

# ---------- Инициализация планировщика (запуск при старте бота) ----------
async def setup_scheduler(bot: Bot):
    # Удаляем все существующие джобы, чтобы избежать дублей при перезапуске
    scheduler.remove_all_jobs()
    
    async with async_session() as session:
        # Утренние и вечерние сообщения для активных пользователей
        users = await session.execute(select(User).where(User.is_active == True))
        for user in users.scalars():
            if user.morning_enabled:
                h, m = map(int, user.morning_time.split(':'))
                scheduler.add_job(
                    send_morning, CronTrigger(hour=h, minute=m),
                    args=[bot, user.tg_id, user.morning_text],
                    id=f"morning_{user.tg_id}",
                    replace_existing=True
                )
            if user.evening_enabled:
                h, m = map(int, user.evening_time.split(':'))
                scheduler.add_job(
                    send_evening, CronTrigger(hour=h, minute=m),
                    args=[bot, user.tg_id, user.evening_text],
                    id=f"evening_{user.tg_id}",
                    replace_existing=True
                )
        
        # Напоминания о привычках
        habits = await session.execute(select(Habit).where(Habit.is_active == True))
        for habit in habits.scalars():
            h, m = map(int, habit.time.split(':'))
            scheduler.add_job(
                send_habit_reminder, CronTrigger(hour=h, minute=m),
                args=[bot, habit],
                id=f"habit_{habit.id}",
                replace_existing=True
            )
        
        # Напоминания о событиях (только будущие, с ненулевым уведомлением)
        events = await session.execute(
            select(Event).where(Event.date >= date.today(), Event.notify_before.isnot(None))
        )
        for event in events.scalars():
            schedule_event_reminder(bot, event)
    
    scheduler.start()

# ---------- Функции отправки ----------
async def send_morning(bot: Bot, tg_id: int, text: str):
    await bot.send_message(tg_id, f"🌅 {text}")

async def send_evening(bot: Bot, tg_id: int, text: str):
    await bot.send_message(tg_id, f"🌙 {text}")

async def send_habit_reminder(bot: Bot, habit: Habit):
    # Проверим, нужно ли сегодня напоминать (по дням недели)
    from datetime import date
    weekday = date.today().isoweekday()  # 1=пн ... 7=вс
    freq = habit.frequency
    if freq.lower() == "ежедневно":
        pass
    else:
        # ожидаем строку "1 3 5" или подобное
        try:
            days = list(map(int, freq.split()))
            if weekday not in days:
                return
        except:
            pass
    await bot.send_message(
        habit.user_id,
        f"⏰ Напоминание о привычке: <b>{habit.name}</b>\n{habit.description or ''}\nВыполнили?",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"habit_done_{habit.id}"),
             InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"habit_skip_{habit.id}")]
        ])
    )

# ---------- Планирование напоминания о событии ----------
def schedule_event_reminder(bot: Bot, event: Event):
    if not event.notify_before:
        return
    # Определяем время отправки
    event_datetime = datetime.combine(event.date, datetime.strptime(event.time, "%H:%M").time() if event.time else datetime.min.time())
    delta_hours = {
        '24h': 24, '12h': 12, '7h': 7, '5h': 5, '3h': 3, '1h': 1
    }.get(event.notify_before)
    if delta_hours is None:
        return
    trigger_time = event_datetime - timedelta(hours=delta_hours)
    if trigger_time < datetime.now():
        return
    scheduler.add_job(
        send_event_reminder, DateTrigger(run_date=trigger_time),
        args=[bot, event],
        id=f"event_{event.id}",
        replace_existing=True
    )

async def send_event_reminder(bot: Bot, event: Event):
    text = f"📅 Напоминание о событии: <b>{event.title}</b>\n"
    if event.description:
        text += f"{event.description}\n"
    text += f"🗓 {event.date}"
    if event.time:
        text += f" в {event.time}"
    await bot.send_message(event.user_id, text)

# ---------- Функции обновления джобов (вызывать при изменении настроек пользователя) ----------
async def update_user_morning_job(bot: Bot, user_id: int, time_str: str, text: str, enabled: bool):
    job_id = f"morning_{user_id}"
    if enabled:
        h, m = map(int, time_str.split(':'))
        scheduler.add_job(send_morning, CronTrigger(hour=h, minute=m), args=[bot, user_id, text], id=job_id, replace_existing=True)
    else:
        scheduler.remove_job(job_id)

async def update_user_evening_job(bot: Bot, user_id: int, time_str: str, text: str, enabled: bool):
    job_id = f"evening_{user_id}"
    if enabled:
        h, m = map(int, time_str.split(':'))
        scheduler.add_job(send_evening, CronTrigger(hour=h, minute=m), args=[bot, user_id, text], id=job_id, replace_existing=True)
    else:
        scheduler.remove_job(job_id)

async def update_habit_job(bot: Bot, habit: Habit):
    job_id = f"habit_{habit.id}"
    if habit.is_active:
        h, m = map(int, habit.time.split(':'))
        scheduler.add_job(send_habit_reminder, CronTrigger(hour=h, minute=m), args=[bot, habit], id=job_id, replace_existing=True)
    else:
        scheduler.remove_job(job_id)

async def update_event_job(bot: Bot, event: Event):
    job_id = f"event_{event.id}"
    scheduler.remove_job(job_id)
    if event.notify_before and event.date >= date.today():
        schedule_event_reminder(bot, event)

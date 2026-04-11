from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from datetime import datetime, date, timedelta
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from db.db import async_session
from db.models import User, Habit, Event, TimeCapsule

scheduler = AsyncIOScheduler(timezone="Europe/Moscow")

async def setup_scheduler(bot: Bot):
    scheduler.remove_all_jobs()
    async with async_session() as session:
        # Утренние и вечерние сообщения
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
        # Привычки
        habits = await session.execute(select(Habit).where(Habit.is_active == True))
        for habit in habits.scalars():
            h, m = map(int, habit.time.split(':'))
            scheduler.add_job(
                send_habit_reminder, CronTrigger(hour=h, minute=m),
                args=[bot, habit],
                id=f"habit_{habit.id}",
                replace_existing=True
            )
        # События (напоминания)
        events = await session.execute(
            select(Event).where(Event.date >= date.today(), Event.notify_before.isnot(None))
        )
        for event in events.scalars():
            schedule_event_reminder(bot, event)
        # Капсулы времени – проверка раз в день
        scheduler.add_job(
            check_time_capsules, CronTrigger(hour=0, minute=5),
            args=[bot],
            id="check_capsules",
            replace_existing=True
        )
    scheduler.start()

async def send_morning(bot: Bot, tg_id: int, text: str):
    await bot.send_message(tg_id, f"🌅 {text}")

async def send_evening(bot: Bot, tg_id: int, text: str):
    await bot.send_message(tg_id, f"🌙 {text}")

async def send_habit_reminder(bot: Bot, habit: Habit):
    weekday = date.today().isoweekday()
    freq = habit.frequency
    if freq == "everyday":
        pass
    elif freq.startswith("month_days:"):
        try:
            days = list(map(int, freq.split(":")[1].split(",")))
            if date.today().day not in days:
                return
        except:
            return
    else:
        try:
            days = list(map(int, freq.split(",")))
            if weekday not in days:
                return
        except:
            pass
    async with async_session() as session:
        user = await session.get(User, habit.user_id)
        if user:
            await bot.send_message(
                user.tg_id,
                f"⏰ Напоминание о привычке: <b>{habit.name}</b>\n{habit.description or ''}\nВыполнили?",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"habit_done_{habit.id}"),
                     InlineKeyboardButton(text="⏭ Пропустить", callback_data=f"habit_skip_{habit.id}")]
                ])
            )

def schedule_event_reminder(bot: Bot, event: Event):
    if not event.notify_before:
        return
    event_datetime = datetime.combine(event.date, datetime.strptime(event.time, "%H:%M").time() if event.time else datetime.min.time())
    delta_hours = {'24h':24, '12h':12, '7h':7, '5h':5, '3h':3, '1h':1}.get(event.notify_before)
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
    async with async_session() as session:
        user = await session.get(User, event.user_id)
        if user:
            text = f"📅 Напоминание о событии: <b>{event.title}</b>\n"
            if event.description:
                text += f"{event.description}\n"
            text += f"🗓 {event.date.strftime('%d.%m.%Y')}"
            if event.time:
                text += f" в {event.time}"
            await bot.send_message(user.tg_id, text)

async def check_time_capsules(bot: Bot):
    today = date.today()
    async with async_session() as session:
        capsules = await session.execute(
            select(TimeCapsule).where(TimeCapsule.open_date <= today, TimeCapsule.is_opened == False)
        )
        for capsule in capsules.scalars():
            user = await session.get(User, capsule.user_id)
            if user:
                text = f"📦 <b>Ваша капсула времени открылась!</b>\n\n<b>{capsule.title}</b>\n\n{capsule.content}\n\n📅 Создана: {capsule.created_at.strftime('%d.%m.%Y')}"
                await bot.send_message(user.tg_id, text)
                capsule.is_opened = True
                await session.commit()

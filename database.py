import asyncio
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy import (
    create_async_engine, AsyncSession, Column, Integer, 
    String, DateTime, Boolean, Text, ForeignKey, select, and_, or_
)
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import declarative_base, relationship
from config import settings
Base = declarative_base()
class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False, index=True)
    username = Column(String(100))
    first_name = Column(String(100))
    last_name = Column(String(100))
    registered_at = Column(DateTime, default=datetime.utcnow)
    
    # Level system
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    streak = Column(Integer, default=0)
    last_activity = Column(DateTime)
    
    # PIN for private section
    pin_code = Column(String(4))
    pin_attempts = Column(Integer, default=0)
    pin_blocked_until = Column(DateTime)
    
    # Quiet mode
    quiet_mode_start = Column(String(5))  # HH:MM format
    quiet_mode_end = Column(String(5))
    
    # Notifications
    notifications_enabled = Column(Boolean, default=True)
    habit_notifications = Column(Boolean, default=True)
    planner_notifications = Column(Boolean, default=True)
    cycle_notifications = Column(Boolean, default=True)
    morning_night_notifications = Column(Boolean, default=True)
    
    # Relationships
    habits = relationship("Habit", back_populates="user", cascade="all, delete-orphan")
    events = relationship("Event", back_populates="user", cascade="all, delete-orphan")
    private_entries = relationship("PrivateEntry", back_populates="user", cascade="all, delete-orphan")
    cycle_tracker = relationship("CycleTracker", back_populates="user", uselist=False, cascade="all, delete-orphan")
    diary_entries = relationship("DiaryEntry", back_populates="user", cascade="all, delete-orphan")
    cycle_logs = relationship("CycleLog", back_populates="user", cascade="all, delete-orphan")
class Habit(Base):
    """Модель привычки"""
    __tablename__ = "habits"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Reminder settings
    reminder_time = Column(String(5))  # HH:MM
    reminder_days = Column(String(20))  # JSON: [1,2,3,4,5,6,7] - дни недели
    reminder_interval = Column(Integer)  # минуты между повторами
    max_reminders = Column(Integer, default=3)
    
    # Status
    is_active = Column(Boolean, default=True)
    disabled_today = Column(Boolean, default=False)
    disabled_date = Column(DateTime)
    
    # Stats
    total_completions = Column(Integer, default=0)
    current_streak = Column(Integer, default=0)
    best_streak = Column(Integer, default=0)
    
    user = relationship("User", back_populates="habits")
    completions = relationship("HabitCompletion", back_populates="habit", cascade="all, delete-orphan")
class HabitCompletion(Base):
    """Выполнение привычки"""
    __tablename__ = "habit_completions"
    
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey("habits.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String(20))  # completed, skipped
    
    habit = relationship("Habit", back_populates="completions")
class Event(Base):
    """Событие планировщика"""
    __tablename__ = "events"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    event_date = Column(DateTime, nullable=False)
    event_time = Column(String(5))  # HH:MM
    
    # Notifications (JSON list of hours before: [24, 12, 3, 1])
    notifications = Column(String(100), default="[1]")
    
    # Status
    status = Column(String(20), default="pending")  # pending, completed, skipped, postponed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="events")
class PrivateEntry(Base):
    """Запись в приватном разделе"""
    __tablename__ = "private_entries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="private_entries")
class CycleTracker(Base):
    """Трекер цикла"""
    __tablename__ = "cycle_trackers"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    
    # Cycle settings
    cycle_length = Column(Integer, default=28)
    period_length = Column(Integer, default=5)
    
    # Current cycle
    last_period_start = Column(DateTime)
    next_period_start = Column(DateTime)
    ovulation_date = Column(DateTime)
    
    # Notifications
    notify_before_period = Column(Boolean, default=True)
    notify_before_ovulation = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="cycle_tracker")
class CycleLog(Base):
    """Ежедневные записи о самочувствии"""
    __tablename__ = "cycle_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    log_date = Column(DateTime, default=datetime.utcnow)
    
    # Wellness metrics (1-10 scale)
    mood = Column(Integer)
    pain = Column(Integer)
    energy = Column(Integer)
    sleep = Column(Integer)
    
    # Notes
    notes = Column(Text)
    
    user = relationship("User", back_populates="cycle_logs")
class DiaryEntry(Base):
    """Записи дневника"""
    __tablename__ = "diary_entries"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="diary_entries")
class AdminMessage(Base):
    """Утренние/ночные сообщения админа"""
    __tablename__ = "admin_messages"
    
    id = Column(Integer, primary_key=True)
    message_type = Column(String(20))  # morning, night
    content = Column(Text, nullable=False)
    scheduled_time = Column(String(5))  # HH:MM
    is_active = Column(Boolean, default=True)
class CycleTip(Base):
    """Советы по фазам цикла"""
    __tablename__ = "cycle_tips"
    
    id = Column(Integer, primary_key=True)
    phase = Column(String(50))  # menstruation, follicular, ovulation, luteal
    content = Column(Text, nullable=False)
# Database Engine
engine = create_async_engine(
    settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://"),
    echo=settings.DEBUG
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
async def init_db():
    """Инициализация базы данных"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
async def get_session() -> AsyncSession:
    """Получение сессии БД"""
    async with async_session() as session:
        return session
# User operations
async def get_user(telegram_id: int) -> Optional[User]:
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()
async def create_user(telegram_id: int, username: str, first_name: str, last_name: str = None) -> User:
    async with async_session() as session:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
async def update_user_xp(user_id: int, xp_amount: int):
    """Обновление XP пользователя"""
    from config import LEVEL_THRESHOLDS
    
    async with async_session() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        
        if user:
            user.xp += xp_amount
            # Check level up
            for level, threshold in sorted(LEVEL_THRESHOLDS.items(), reverse=True):
                if user.xp >= threshold:
                    user.level = level
                    break
            await session.commit()
# Habit operations
async def get_user_habits(user_id: int) -> List[Habit]:
    async with async_session() as session:
        result = await session.execute(
            select(Habit).where(Habit.user_id == user_id, Habit.is_active == True)
        )
        return result.scalars().all()
async def create_habit(user_id: int, name: str, description: str = None, 
                       reminder_time: str = None, reminder_days: str = None) -> Habit:
    async with async_session() as session:
        habit = Habit(
            user_id=user_id,
            name=name,
            description=description,
            reminder_time=reminder_time,
            reminder_days=reminder_days
        )
        session.add(habit)
        await session.commit()
        await session.refresh(habit)
        return habit
async def complete_habit(habit_id: int, status: str = "completed"):
    """Отметить привычку выполненной"""
    async with async_session() as session:
        result = await session.execute(select(Habit).where(Habit.id == habit_id))
        habit = result.scalar_one_or_none()
        
        if habit:
            habit.total_completions += 1
            habit.current_streak += 1
            if habit.current_streak > habit.best_streak:
                habit.best_streak = habit.current_streak
            
            completion = HabitCompletion(habit_id=habit_id, status=status)
            session.add(completion)
            await session.commit()
            
            # Add XP
            await update_user_xp(habit.user_id, 10)
# Event operations
async def get_user_events(user_id: int) -> List[Event]:
    async with async_session() as session:
        result = await session.execute(
            select(Event).where(
                Event.user_id == user_id,
                Event.status.in_(["pending", "postponed"]),
                Event.event_date >= datetime.utcnow()
            ).order_by(Event.event_date)
        )
        return result.scalars().all()
async def create_event(user_id: int, title: str, event_date: datetime, 
                       description: str = None, event_time: str = None,
                       notifications: str = "[1]") -> Event:
    async with async_session() as session:
        event = Event(
            user_id=user_id,
            title=title,
            description=description,
            event_date=event_date,
            event_time=event_time,
            notifications=notifications
        )
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event
# Cycle operations
async def get_or_create_cycle_tracker(user_id: int) -> CycleTracker:
    async with async_session() as session:
        result = await session.execute(
            select(CycleTracker).where(CycleTracker.user_id == user_id)
        )
        tracker = result.scalar_one_or_none()
        
        if not tracker:
            tracker = CycleTracker(user_id=user_id)
            session.add(tracker)
            await session.commit()
            await session.refresh(tracker)
        
        return tracker
async def update_cycle_tracker(user_id: int, last_period_start: datetime,
                                cycle_length: int = 28, period_length: int = 5):
    async with async_session() as session:
        result = await session.execute(
            select(CycleTracker).where(CycleTracker.user_id == user_id)
        )
        tracker = result.scalar_one_or_none()
        
        if tracker:
            tracker.last_period_start = last_period_start
            tracker.cycle_length = cycle_length
            tracker.period_length = period_length
            tracker.next_period_start = last_period_start + timedelta(days=cycle_length)
            tracker.ovulation_date = last_period_start + timedelta(days=cycle_length - 14)
            await session.commit()
# Admin operations
async def add_admin_message(message_type: str, content: str, scheduled_time: str):
    async with async_session() as session:
        msg = AdminMessage(
            message_type=message_type,
            content=content,
            scheduled_time=scheduled_time
        )
        session.add(msg)
        await session.commit()
async def get_admin_messages(message_type: str) -> List[AdminMessage]:
    async with async_session() as session:
        result = await session.execute(
            select(AdminMessage).where(
                AdminMessage.message_type == message_type,
                AdminMessage.is_active == True
            )
        )
        return result.scalars().all()
async def add_cycle_tip(phase: str, content: str):
    async with async_session() as session:
        tip = CycleTip(phase=phase, content=content)
        session.add(tip)
        await session.commit()
async def get_all_users() -> List[User]:
    async with async_session() as session:
        result = await session.execute(select(User))
        return result.scalars().all()

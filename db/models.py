from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(Integer, unique=True)
    name = Column(String)
    reg_date = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)
    morning_time = Column(String, default="08:00")
    evening_time = Column(String, default="23:00")
    morning_enabled = Column(Boolean, default=True)
    evening_enabled = Column(Boolean, default=True)
    morning_text = Column(String, default="Доброе утро! ☀️")
    evening_text = Column(String, default="Спокойной ночи! 🌙")
    cycle_start_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, nullable=True)
    period_length = Column(Integer, nullable=True)
    pin_hash = Column(String, nullable=True)
    last_pms_notification = Column(Date, nullable=True)  # для предотвращения дублирования

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String)
    description = Column(Text)
    time = Column(String)
    frequency = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    is_active = Column(Boolean, default=True)

class HabitLog(Base):
    __tablename__ = 'habit_logs'
    id = Column(Integer, primary_key=True)
    habit_id = Column(Integer, ForeignKey('habits.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now().date)
    completed = Column(Boolean, default=False)
    skipped = Column(Boolean, default=False)

class Event(Base):
    __tablename__ = 'events'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    description = Column(Text, nullable=True)
    date = Column(Date)
    time = Column(String, nullable=True)
    notify_before = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

class CycleLog(Base):
    __tablename__ = 'cycle_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now().date)
    mood = Column(Integer, nullable=True)      # 1-5
    pain = Column(Integer, nullable=True)      # 1-5
    energy = Column(Integer, nullable=True)    # 1-5
    sleep = Column(Integer, nullable=True)     # 1-5
    headache = Column(Boolean, default=False)  # головная боль
    bloating = Column(Boolean, default=False)  # вздутие
    acne = Column(Boolean, default=False)      # акне
    notes = Column(Text, nullable=True)

class CycleTip(Base):
    __tablename__ = 'cycle_tips'
    id = Column(Integer, primary_key=True)
    phase = Column(String)  # 'menstruation', 'follicular', 'ovulation', 'luteal'
    tip = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

class DiaryEntry(Base):
    __tablename__ = 'diary'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    emotion = Column(String, nullable=True)
    date = Column(Date, default=datetime.now().date)
    tags = Column(String, nullable=True)

class SecretNote(Base):
    __tablename__ = 'secret_notes'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

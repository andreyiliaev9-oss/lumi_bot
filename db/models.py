from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, BigInteger, Text, ForeignKey
from sqlalchemy.orm import DeclarativeBase
from datetime import datetime

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    name = Column(String)
    reg_date = Column(DateTime, default=datetime.now)
    
    # Настройки времени уведомлений
    morning_time = Column(String, default="08:00")
    evening_time = Column(String, default="19:00")
    
    # Секретный доступ
    private_pin_hash = Column(String, nullable=True)
    
    # Параметры цикла
    cycle_start_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, default=28)
    period_length = Column(Integer, default=5)
    
    # Счётчики для красивого профиля
    completed_habits = Column(Integer, default=0)
    missed_habits = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    diary_count = Column(Integer, default=0)

class DiaryEntry(Base):
    __tablename__ = 'diary'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    emotion = Column(String, nullable=True)
    date = Column(Date, default=datetime.now().date)
    tags = Column(String, nullable=True)

class CycleTip(Base):
    __tablename__ = 'cycle_tips'
    id = Column(Integer, primary_key=True)
    phase = Column(String) # menstruation, follicular, ovulation, luteal
    text = Column(Text)

class Compliment(Base):
    __tablename__ = 'compliments'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    is_active = Column(Boolean, default=True)

class Habit(Base):
    __tablename__ = 'habits'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    reminder_time = Column(String)
    created_at = Column(Date, default=datetime.now().date)

class Task(Base):
    __tablename__ = 'tasks'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    title = Column(String)
    due_date = Column(DateTime)
    is_completed = Column(Boolean, default=False)

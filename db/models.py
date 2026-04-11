from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, BigInteger, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    name = Column(String)
    reg_date = Column(DateTime, default=datetime.now)
    
    # Настройки времени (ТЗ 2.8)
    morning_time = Column(String, default="19:00")
    evening_time = Column(String, default="23:00")
    
    # Безопасность
    private_pin_hash = Column(String, nullable=True)
    
    # Данные цикла (ТЗ 2.2.2)
    cycle_start_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, default=28)
    period_length = Column(Integer, default=5)
    
    # Статистика для профиля (ТЗ 2.3)
    completed_habits = Column(Integer, default=0)
    missed_habits = Column(Integer, default=0)
    completed_tasks = Column(Integer, default=0)
    diary_count = Column(Integer, default=0)

class CycleTip(Base):
    __tablename__ = 'cycle_tips'
    id = Column(Integer, primary_key=True)
    phase = Column(String) # menstruation, follicular, ovulation, luteal
    text = Column(Text)

class CycleLog(Base):
    __tablename__ = 'cycle_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now().date)
    mood = Column(Integer)
    pain = Column(Integer)
    energy = Column(Integer)
    sleep = Column(Integer)
    symptoms = Column(String, nullable=True)
    notes = Column(Text, nullable=True)

class DiaryEntry(Base):
    __tablename__ = 'diary'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    text = Column(Text)
    emotion = Column(String, nullable=True)
    date = Column(Date, default=datetime.now().date)
    tags = Column(String, nullable=True)

class Compliment(Base):
    __tablename__ = 'compliments'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    is_active = Column(Boolean, default=True)

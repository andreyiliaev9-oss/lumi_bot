from sqlalchemy import Column, Integer, String, Boolean, DateTime, Date, BigInteger, Text, ForeignKey
from datetime import datetime
from .db import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True)
    name = Column(String)
    reg_date = Column(DateTime, default=datetime.now)
    
    # Настройки
    morning_time = Column(String, default="08:00")
    evening_time = Column(String, default="23:00")
    
    # Безопасность
    private_pin_hash = Column(String, nullable=True) # Здесь будет зашифрованный PIN
    
    # Цикл
    cycle_start_date = Column(Date, nullable=True)
    cycle_length = Column(Integer, default=28)
    period_length = Column(Integer, default=5)
    
    # Статистика
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

class CycleLog(Base):
    __tablename__ = 'cycle_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    date = Column(Date, default=datetime.now().date)
    mood = Column(Integer)
    pain = Column(Integer)
    energy = Column(Integer)
    sleep = Column(Integer)
    notes = Column(Text, nullable=True)

# Также добавим таблицу для комплиментов
class Compliment(Base):
    __tablename__ = 'compliments'
    id = Column(Integer, primary_key=True)
    text = Column(Text)
    is_active = Column(Boolean, default=True)

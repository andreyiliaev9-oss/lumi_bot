import os
from pydantic_settings import BaseSettings
from pydantic import Field
class Settings(BaseSettings):
    """Конфигурация бота"""
    
    # Bot
    BOT_TOKEN: str = Field(default="", env="BOT_TOKEN")
    BOT_NAME: str = Field(default="ЛЮМИ", env="BOT_NAME")
    DEBUG: bool = Field(default=False, env="DEBUG")
    
    # Admin
    ADMIN_ID: int = Field(default=0, env="ADMIN_ID")
    
    # Database
    DATABASE_URL: str = Field(default="sqlite:///lumi_bot.db", env="DATABASE_URL")
    
    # Security
    MAX_PIN_ATTEMPTS: int = 3
    PIN_BLOCK_MINUTES: int = 5
    PRIVATE_AUTO_LOGOUT_MINUTES: int = 5
    
    # Habits
    MAX_HABIT_REMINDERS: int = 3
    
    # Cycle
    DEFAULT_CYCLE_LENGTH: int = 28
    DEFAULT_PERIOD_LENGTH: int = 5
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
settings = Settings()
# XP System
XP_CONFIG = {
    "habit_complete": 10,
    "habit_streak_7": 50,
    "habit_streak_30": 200,
    "task_complete": 15,
    "diary_entry": 5,
    "cycle_log": 5,
}
# Level thresholds
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 300,
    4: 600,
    5: 1000,
    6: 1500,
    7: 2100,
    8: 2800,
    9: 3600,
    10: 4500,
}
# Notification time options (hours before event)
NOTIFICATION_TIMES = {
    "24ч": 24,
    "12ч": 12,
    "7ч": 7,
    "5ч": 5,
    "3ч": 3,
    "1ч": 1,
}

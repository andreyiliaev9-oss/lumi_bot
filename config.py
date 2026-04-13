# /root/lumi_bot/config.py

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

# Загружаем .env из корня проекта
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, field_name: str) -> int:
    if value is None or value.strip() == "":
        raise ValueError(f"{field_name} is required in .env")
    try:
        return int(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be integer, got: {value}") from exc


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    ADMIN_ID: int
    DATABASE_URL: str
    DEBUG: bool
    TIMEZONE: str
    MORNING_DEFAULT_TIME: str
    NIGHT_DEFAULT_TIME: str


def _build_settings() -> Settings:
    bot_token = (os.getenv("BOT_TOKEN") or "").strip()
    if not bot_token:
        raise ValueError("BOT_TOKEN is required in .env")

    admin_id = _to_int(os.getenv("ADMIN_ID"), "ADMIN_ID")

    database_url = (os.getenv("DATABASE_URL") or "sqlite:///lumi_bot.db").strip()
    debug = _to_bool(os.getenv("DEBUG"), default=False)
    timezone = (os.getenv("TIMEZONE") or "Europe/Moscow").strip()
    morning_time = (os.getenv("MORNING_DEFAULT_TIME") or "08:00").strip()
    night_time = (os.getenv("NIGHT_DEFAULT_TIME") or "22:00").strip()

    return Settings(
        BOT_TOKEN=bot_token,
        ADMIN_ID=admin_id,
        DATABASE_URL=database_url,
        DEBUG=debug,
        TIMEZONE=timezone,
        MORNING_DEFAULT_TIME=morning_time,
        NIGHT_DEFAULT_TIME=night_time,
    )


settings = _build_settings()

# XP -> уровень
LEVEL_THRESHOLDS = {
    1: 0,
    2: 100,
    3: 250,
    4: 450,
    5: 700,
    6: 1000,
    7: 1400,
    8: 1850,
    9: 2350,
    10: 2900,
}

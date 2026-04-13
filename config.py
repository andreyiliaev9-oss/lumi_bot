cat > config.py << 'EOF'
import os
from dotenv import load_dotenv

load_dotenv()


def str_to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "y", "on")


class Settings:
    def __init__(self):
        self.BOT_TOKEN = os.getenv("BOT_TOKEN", "")
        self.ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
        self.DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///lumi.db")
        self.DEBUG = str_to_bool(os.getenv("DEBUG"), False)

        self.TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")
        self.DEFAULT_MORNING_TIME = os.getenv("DEFAULT_MORNING_TIME", "08:00")
        self.DEFAULT_NIGHT_TIME = os.getenv("DEFAULT_NIGHT_TIME", "22:00")

        self.PIN_LENGTH = int(os.getenv("PIN_LENGTH", "4"))
        self.PIN_MAX_ATTEMPTS = int(os.getenv("PIN_MAX_ATTEMPTS", "3"))
        self.PIN_BLOCK_MINUTES = int(os.getenv("PIN_BLOCK_MINUTES", "5"))
        self.PRIVATE_AUTO_LOGOUT_MINUTES = int(os.getenv("PRIVATE_AUTO_LOGOUT_MINUTES", "5"))

        self.HABIT_MAX_REPEAT = int(os.getenv("HABIT_MAX_REPEAT", "3"))
        self.HABIT_REPEAT_INTERVAL_MINUTES = int(os.getenv("HABIT_REPEAT_INTERVAL_MINUTES", "60"))

        self.DEFAULT_QUIET_START = os.getenv("DEFAULT_QUIET_START", "22:00")
        self.DEFAULT_QUIET_END = os.getenv("DEFAULT_QUIET_END", "09:00")

        self.SCHEDULER_ENABLED = str_to_bool(os.getenv("SCHEDULER_ENABLED"), True)

    def validate(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не найден. Добавь его в .env")
        if self.ADMIN_ID < 0:
            raise ValueError("ADMIN_ID должен быть >= 0")


settings = Settings()
settings.validate()

LEVEL_THRESHOLDS = {
    1: 0,
    2: 50,
    3: 120,
    4: 220,
    5: 350,
    6: 500,
    7: 700,
    8: 950,
    9: 1250,
    10: 1600,
}
EOF

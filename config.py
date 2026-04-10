import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
DB_URL = os.getenv("DB_URL", f"sqlite+aiosqlite:///{BASE_DIR}/data/lumi.db")
TIMEZONE = os.getenv("TIMEZONE", "Europe/Moscow")

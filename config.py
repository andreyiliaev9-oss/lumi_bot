import os
from dotenv import load_dotenv

load_dotenv()

# Основные данные из .env
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

# Путь к базе данных
DB_URL = "sqlite+aiosqlite:///data/lumi.db"

# Стили оформления (фиолетовый вайб)
THEME_COLOR = "💜"
BOT_NAME = "ЛЮМИ"

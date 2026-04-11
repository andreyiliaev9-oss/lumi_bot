import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
# Путь к базе данных, как в ТЗ
DB_URL = "sqlite+aiosqlite:///data/lumi.db"

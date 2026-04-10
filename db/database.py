import aiosqlite

DB_NAME = "lumi_database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        # Таблица пользователей (добавили gender)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                gender TEXT,
                streak_days INTEGER DEFAULT 0,
                joined_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_registered INTEGER DEFAULT 0
            )
        """)
        # Таблица разовых задач
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                task_time DATETIME,
                is_notified INTEGER DEFAULT 0
            )
        """)
        # Таблица привычек
        await db.execute("""
            CREATE TABLE IF NOT EXISTS habits (
                habit_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                remind_time TEXT,
                streak INTEGER DEFAULT 0,
                last_completed DATE
            )
        """)
        await db.commit()

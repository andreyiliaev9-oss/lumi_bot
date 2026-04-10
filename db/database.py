import aiosqlite

DB_NAME = "lumi_database.db"

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                morning_time TEXT DEFAULT '09:00',
                evening_time TEXT DEFAULT '23:00',
                morning_msg TEXT DEFAULT 'Доброе утро! Пусть этот день пройдет легко.',
                evening_msg TEXT DEFAULT 'Доброй ночи, время восстановить силы.',
                morning_enabled INTEGER DEFAULT 1,
                evening_enabled INTEGER DEFAULT 1,
                streak_days INTEGER DEFAULT 0,
                last_active DATE,
                support_banned INTEGER DEFAULT 0,
                custom_name TEXT
            )
        """)
        
        await db.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT,
                task_time TIMESTAMP,
                remind_type TEXT,
                is_notified INTEGER DEFAULT 0
            )
        """)
        await db.commit()

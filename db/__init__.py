        # Таблица для планировщика
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


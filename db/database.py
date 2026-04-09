import aiosqlite

# Имя файла базы данных (будет лежать в корне проекта рядом с bot.py)
DB_NAME = "lumi_database.db"


async def init_db():
    """
    Функция инициализации базы данных.
    Вызывается один раз при запуске бота. Создает таблицы, если их нет.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        # Создаем таблицу пользователей
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT DEFAULT NULL,
                first_name TEXT NOT NULL,
                joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Сохраняем изменения
        await db.commit()

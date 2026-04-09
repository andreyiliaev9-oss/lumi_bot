import aiosqlite
from db.database import DB_NAME


async def add_user(user_id: int, username: str, first_name: str):
    """
    Добавляет нового пользователя в базу данных.
    Используем INSERT OR IGNORE, чтобы бот не выдавал ошибку, 
    если пользователь уже есть в базе (например, нажал /start повторно).
    """
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute(
            "INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)",
            (user_id, username, first_name)
        )
        await db.commit()

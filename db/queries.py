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
async def get_user(user_id: int):
    """
    Проверяет, есть ли пользователь в базе.
    Если есть - возвращает его данные. Если нет - возвращает None.
    """
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

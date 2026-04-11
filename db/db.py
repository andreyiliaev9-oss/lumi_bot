from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import DB_URL
from .models import Base

# Создаем движок с поддержкой асинхронности
engine = create_async_engine(
    DB_URL,
    echo=False, # Поставь True, если захочешь видеть все SQL-запросы в консоли
    future=True
)

# Фабрика сессий для работы с запросами
async_session = async_sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

# Функция для инициализации базы при старте
async def init_db():
    async with engine.begin() as conn:
        # Эта команда создает все таблицы из файла models.py, если их еще нет
        await conn.run_sync(Base.metadata.create_all)

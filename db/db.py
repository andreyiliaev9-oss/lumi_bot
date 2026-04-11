from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import DB_URL
from .models import Base

# Создаем движок
engine = create_async_engine(DB_URL, echo=False)

# Используем современный async_sessionmaker
async_session = async_sessionmaker(
    bind=engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# Исправленная функция инициализации
async def init_db():
    async with engine.begin() as conn:
        # Добавили скобки (), чтобы таблицы реально создались
        await conn.run_sync(Base.metadata.create_all) 
    print("🗄️ База данных и таблицы проверены/созданы")

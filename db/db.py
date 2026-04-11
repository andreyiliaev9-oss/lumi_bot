from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from config import DB_URL

# Создаем "движок" для общения с файлом lumi.db
engine = create_async_engine(DB_URL, echo=False)

# Создаем фабрику сессий (чтобы открывать/закрывать базу)
async_session = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для всех таблиц
class Base(DeclarativeBase):
    pass

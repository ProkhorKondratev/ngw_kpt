from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

conn_str = "sqlite+aiosqlite:///data/database/database.db"
engine = create_async_engine(conn_str, echo=False)
new_session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def create_tables():
    print("Создание таблиц")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    print("Удаление таблиц")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

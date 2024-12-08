from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, select
from sqlalchemy.orm import Mapped, mapped_column
from zoneinfo import ZoneInfo

from .engine import Base, new_session


class Table(Base):
    __abstract__ = True

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("UTC")),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(ZoneInfo("UTC")),
        onupdate=lambda: datetime.now(ZoneInfo("UTC")),
    )

    @classmethod
    async def get(cls, id):
        async with new_session() as session:
            return await session.get(cls, id)

    @classmethod
    async def all(cls):
        async with new_session() as session:
            result = await session.execute(select(cls))
            return result.scalars().all()


class Task(Table):
    __tablename__ = "tasks"

    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))

    celery_id: Mapped[str] = mapped_column(nullable=True)
    task_id: Mapped[str] = mapped_column(nullable=True)

    source_file: Mapped[str] = mapped_column(nullable=True)
    kpt_file: Mapped[str] = mapped_column(nullable=True)
    status: Mapped[str] = mapped_column(nullable=True)
    error: Mapped[str] = mapped_column(nullable=True)

    options: Mapped[dict] = mapped_column(JSON, nullable=True)


class Group(Table):
    __tablename__ = "groups"

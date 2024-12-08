from collections import defaultdict
from contextlib import asynccontextmanager
from uuid import uuid4

from sqlalchemy.sql import select

from app.db import GroupTable, TaskTable, new_session


@asynccontextmanager
async def transaction(session: None = None):
    if session is None:
        async with new_session() as new_sess:
            yield new_sess
    else:
        yield session


class Repository:
    @staticmethod
    async def get_task(task_id: int, base_session=None):
        async with transaction(base_session) as session:
            return await session.get(TaskTable, task_id)

    @staticmethod
    async def get_tasks(group_id: int | None = None, base_session=None):
        async with transaction(base_session) as session:
            statement = select(TaskTable)
            if group_id:
                statement = statement.where(TaskTable.group_id == group_id)
            tasks = await session.execute(statement)
            return tasks.scalars().all()

    @staticmethod
    async def get_group(group_id: int, base_session=None):
        async with transaction(base_session) as session:
            statement = (
                select(
                    GroupTable.id,
                    GroupTable.name,
                    GroupTable.created_at,
                    TaskTable.status,
                )
                .join(TaskTable, TaskTable.group_id == GroupTable.id)
                .where(GroupTable.id == group_id)
            )
            result = await session.execute(statement)

            group = {
                "id": group_id,
                "name": None,
                "created_at": None,
                "statistics": {
                    "loaded": 0,
                    "completed": 0,
                    "failed": 0,
                    "in_progress": 0,
                    "remaining": 0,
                },
            }

            async for row in result:
                if not group["name"]:
                    group["name"] = row.name
                    group["created_at"] = row.created_at

                status = row.status if row.status else "accepted"
                if status == "failed":
                    group["statistics"]["failed"] += 1
                elif status == "completed":
                    group["statistics"]["completed"] += 1
                elif status != "accepted":
                    group["statistics"]["in_progress"] += 1

                group["statistics"]["loaded"] += 1

            group["statistics"]["remaining"] = (
                group["statistics"]["loaded"] - group["statistics"]["completed"] - group["statistics"]["failed"]
            )

            return group

    @staticmethod
    async def get_groups(base_session=None):
        async with transaction(base_session) as session:
            statement = select(
                GroupTable.id,
                GroupTable.name,
                GroupTable.created_at,
                TaskTable.status,
            ).join(TaskTable, TaskTable.group_id == GroupTable.id)

            result = await session.execute(statement)

            groups = defaultdict(
                lambda: {
                    "id": None,
                    "name": None,
                    "created_at": None,
                    "statistics": {
                        "loaded": 0,
                        "completed": 0,
                        "failed": 0,
                        "in_progress": 0,
                        "remaining": 0,
                    },
                }
            )

            for row in result:
                group_id = row.id
                group = groups[group_id]

                if not group["id"]:
                    group["id"] = row.id
                    group["name"] = row.name
                    group["created_at"] = row.created_at

                status = row.status if row.status else "accepted"
                if status == "failed":
                    group["statistics"]["failed"] += 1
                elif status == "completed":
                    group["statistics"]["completed"] += 1
                elif status != "accepted":
                    group["statistics"]["in_progress"] += 1

                group["statistics"]["loaded"] += 1

            for group in groups.values():
                group["statistics"]["remaining"] = (
                    group["statistics"]["loaded"] - group["statistics"]["completed"] - group["statistics"]["failed"]
                )

            return list(groups.values())

    @staticmethod
    async def get_statistics(base_session=None):
        async with transaction(base_session) as session:
            statement = select(TaskTable.status)
            result = await session.execute(statement)

            statistics = {
                "loaded": 0,
                "completed": 0,
                "failed": 0,
                "in_progress": 0,
                "remaining": 0,
            }

            for row in result:
                status = row.status if row.status else "accepted"
                if status == "failed":
                    statistics["failed"] += 1
                elif status == "completed":
                    statistics["completed"] += 1
                elif status != "accepted":
                    statistics["in_progress"] += 1

                statistics["loaded"] += 1

            statistics["remaining"] = statistics["loaded"] - statistics["completed"] - statistics["failed"]

            return statistics

    @staticmethod
    async def update_task(identifier: int, base_session=None, **kwargs):
        async with transaction(base_session) as session:
            task = await session.get(TaskTable, identifier)
            for key, value in kwargs.items():
                setattr(task, key, value)

            if base_session is None:
                await session.commit()
            return task

    @staticmethod
    async def create_group(name: str, base_session=None):
        async with transaction(base_session) as session:
            group = GroupTable(name=name)
            session.add(group)

            if base_session is None:
                await session.commit()
            return group

    @staticmethod
    async def create_task(base_session=None, **kwargs):
        async with transaction(base_session) as session:
            task = TaskTable(**kwargs)
            task.status = "accepted"
            task.celery_id = str(uuid4())
            session.add(task)

            if base_session is None:
                await session.commit()
            return task

    @staticmethod
    async def delete_task(task_id: int, base_session=None):
        async with transaction(base_session) as session:
            task = await session.get(TaskTable, task_id)
            if task:
                await session.delete(task)

                if base_session is None:
                    await session.commit()
            return task

    @staticmethod
    async def delete_group(group_id: int, base_session=None):
        async with transaction(base_session) as session:
            group = await session.get(GroupTable, group_id)
            if group:
                await session.delete(group)

                if base_session is None:
                    await session.commit()

            return group

    @staticmethod
    async def get_working_tasks(base_session=None):
        async with transaction(base_session) as session:
            statement = (
                select(TaskTable.id)
                .where(TaskTable.status.notin_(["completed", "failed"]))
                .order_by(TaskTable.created_at)
            )

            return await session.execute(statement)

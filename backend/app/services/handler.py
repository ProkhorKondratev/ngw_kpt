import asyncio
from uuid import uuid4

from app.models import ProcessingParams
from app.services.worker import celery, collect_kpt

from .repository import Repository, transaction
from .uploader import Uploader


class Handler:
    """Верхнеуровневый класс для выполнения конвертации выписок"""

    @staticmethod
    async def create_tasks(params: ProcessingParams):
        async with transaction() as session:
            files = params.files
            if not params.force_add:
                existing_tasks = await Repository.get_tasks(base_session=session)
                files = list(
                    filter(
                        lambda x: Uploader.get_filename(x.filename) not in [task.name for task in existing_tasks],
                        files,
                    )
                )

            if not files:
                raise Exception("Все файлы уже обработаны")

            files_info = await asyncio.gather(*[Uploader.upload(file) for file in files])
            name = params.name if params.name is not None else files_info[0][1]
            group = await Repository.create_group(name, session)
            await session.commit()

            tasks = await asyncio.gather(
                *[
                    Repository.create_task(
                        session,
                        name=task_name,
                        group_id=group.id,
                        source_file=task_path,
                        options=params.get_params(),
                    )
                    for task_path, task_name in files_info
                ]
            )

            await session.commit()
            task_ids = await asyncio.gather(*[Handler.run_task(task.id, task.celery_id) for task in tasks])

            return group.id, task_ids

    @staticmethod
    async def run_task(task_id: int, celery_id: str):
        collect_kpt.apply_async(
            args=(task_id,),
            task_id=celery_id,
        )
        return task_id

    @staticmethod
    async def restart_task(db_id: int, base_session=None, force=False):
        print("Перезапуск задачи", db_id)
        async with transaction(base_session) as session:
            task = await Repository.get_task(db_id, session)
            celery.control.revoke(task.celery_id, terminate=True)

            new_celery_id = str(uuid4())
            await Uploader.clear_file(task.kpt_file)

            await Repository.update_task(
                db_id,
                session,
                celery_id=new_celery_id,
                kpt_file=None,
                task_id=None if force else task.task_id,
                status="accepted",
                error=None,
            )

            if base_session is None:
                await session.commit()

            await Handler.run_task(db_id, new_celery_id)

    @staticmethod
    async def restart_group(group_id: int):
        async with transaction() as session:
            tasks = await Repository.get_tasks(group_id, session)
            await asyncio.gather(*[Handler.restart_task(task.id, session, force=True) for task in tasks])
            await session.commit()

    @staticmethod
    async def delete_task(task_id: int, base_session=None):
        async with transaction(base_session) as session:
            task = await Repository.delete_task(task_id, session)
            celery.control.revoke(task.celery_id, terminate=True)
            await Uploader.clear_files(task.source_file, task.kpt_file)

            if base_session is None:
                await session.commit()

    @staticmethod
    async def delete_group(group_id: int):
        async with transaction() as session:
            tasks = await Repository.get_tasks(group_id, session)
            await asyncio.gather(*[Handler.delete_task(task.id, session) for task in tasks])
            await Repository.delete_group(group_id, session)
            await session.commit()

    @staticmethod
    async def restart_working_tasks():
        async with transaction() as session:
            tasks = await Repository.get_working_tasks(session)
            await asyncio.gather(*[Handler.restart_task(task.id, session) for task in tasks])
            await session.commit()

    @staticmethod
    async def download_group(group_id: int):
        async with transaction() as session:
            tasks = await Repository.get_tasks(group_id, session)
            paths = [task.kpt_file for task in tasks if task.kpt_file]
            return await Uploader.zip_files(paths)

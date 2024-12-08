import asyncio
import os
import random
import time

import urllib3
from celery import Celery

from .ng_toolbox import NGToolbox
from .parsers import SHPParser, XMLParser
from .repository import Repository
from .uploader import Uploader
from .work_cycle import pause_manager

urllib3.disable_warnings()

celery = Celery(__name__)
celery.conf.broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
celery.conf.result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")


async def check_status(task):
    max_total_time = 60 * 90  # 90 минут
    start_time = time.time()
    max_delay = 60 * 5  # максимальная задержка между попытками
    attempts = 0

    jitter = random.uniform(0, 3)
    await asyncio.sleep(jitter)

    while True:
        if time.time() - start_time > max_total_time:
            raise TimeoutError("Превышено время обработки задачи")

        print(f"Получение статуса задачи {task.task_id}")
        status = NGToolbox.status(task_id=task.task_id)

        if status["state"] == "FAILED":
            raise Exception(status["error"] if status["error"] else "Неизвестная ошибка")

        if status["state"] == "CANCELLED":
            raise Exception("Задача была отменена")

        if status["state"] == "SUCCESS":
            file_url = status["output"][0]["value"]
            file = NGToolbox.download(file_url)
            file_path = await Uploader.save(file, task.name, "data/results/")
            task = await Repository.update_task(task.id, None, kpt_file=file_path)
            return task

        jitter = random.uniform(0, 10)
        sleep_time = min(attempts * 2 + jitter, max_delay)
        print(f"Попытка {attempts + 1} через {sleep_time} секунд")
        await asyncio.sleep(sleep_time)
        attempts += 1


@celery.task()
def collect_kpt(id: int):
    try:

        async def collect_kpt_async(id):
            await pause_manager.wait_if_paused()
            task = await Repository.get_task(id)

            if not task.task_id:
                await Repository.update_task(task.id, None, status="parsing")
                XMLParser.fix_sk_id(task.source_file)
                file_id = NGToolbox.upload(task.source_file)
                task_id = NGToolbox.collect_kpt(file_id, identifier=task.name, **task.options)
                task = await Repository.update_task(task.id, None, task_id=task_id, status="converting")

            task = await check_status(task)

            await Repository.update_task(task.id, None, status="postprocessing")
            SHPParser.fix_crs(task.kpt_file)

            await Repository.update_task(task.id, None, status="completed")

        asyncio.run(collect_kpt_async(id))

    except Exception as e:
        asyncio.run(Repository.update_task(id, None, status="failed", error=str(e)))
        raise e

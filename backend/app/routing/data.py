from fastapi import APIRouter
from fastapi.exceptions import HTTPException
from fastapi.responses import FileResponse, JSONResponse

from app.models import GroupModel, TaskModel
from app.services import Handler, Repository

router = APIRouter()


@router.get("/tasks")
async def get_tasks() -> list[TaskModel]:
    """Получение задач"""
    try:
        tasks_db = await Repository.get_tasks()
        return [TaskModel.model_validate(task) for task in tasks_db]

    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/tasks/{task_id}")
async def get_task(task_id: int) -> TaskModel:
    """Получение задачи"""
    try:
        taskDB = await Repository.get_task(task_id)
        return TaskModel.model_validate(taskDB)

    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/groups")
async def get_groups() -> list[GroupModel]:
    """Получение групп задач"""
    try:
        groups_db = await Repository.get_groups()
        return [GroupModel.model_validate(group) for group in groups_db]
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/groups/{group_id}")
async def get_group(group_id: int) -> GroupModel:
    """Получение группы задач"""
    try:
        group_db = await Repository.get_group(group_id)
        return GroupModel.model_validate(group_db)
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    """Удаление задачи"""
    try:
        await Handler.delete_task(task_id)
        return JSONResponse(status_code=200, content={"message": "Задача успешно удалена"})
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.delete("/groups/{group_id}")
async def delete_group(group_id: int):
    """Удаление группы задач"""
    try:
        await Handler.delete_group(group_id)
        return JSONResponse(status_code=200, content={"message": "Группа успешно удалена"})
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/statistics")
async def get_statistics():
    """Получение статистики по обработке всех задач"""
    try:
        return await Repository.get_statistics()
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/tasks/{task_id}/download")
async def download_task(task_id: int):
    """Скачивание архива с результатами обработки задачи"""
    try:
        task = await Repository.get_task(task_id)
        if task.kpt_file:
            return FileResponse(task.kpt_file, filename=task.name + ".zip")
        else:
            raise HTTPException(status_code=404, detail="Запрошенный файл не найден")
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/source/{task_id}/download/")
async def download_task_source(task_id: int):
    """Скачивание архива с исходными данными задачи"""
    try:
        task = await Repository.get_task(task_id)
        if task.source_file:
            return FileResponse(task.source_file, filename=task.name + ".zip")
        else:
            raise HTTPException(status_code=404, detail="Запрошенный файл не найден")
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e


@router.get("/groups/{group_id}/download")
async def download_group(group_id: int):
    """Скачивание архива с результатами обработки группы"""
    try:
        file = await Handler.download_group(group_id)
        return FileResponse(file)
    except Exception as e:
        # raise HTTPException(status_code=500, detail=str(e))
        raise e

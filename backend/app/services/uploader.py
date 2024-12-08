import asyncio
import os
import zipfile
from pathlib import Path
from uuid import uuid4

import aiofiles
import aiofiles.os as aos
from fastapi import UploadFile


class Uploader:
    @staticmethod
    def get_filename(path: str | None):
        if path is None:
            return str(uuid4())
        return Path(path).stem

    @staticmethod
    async def find_path(folder: str, filename: str):
        if not await aos.path.exists(folder):
            await aos.makedirs(folder)

        base_name, extension = os.path.splitext(filename)
        counter = 1
        full_path = os.path.join(folder, filename)

        while await aos.path.exists(full_path):
            new_filename = f"{base_name}({counter}){extension}"
            full_path = os.path.join(folder, new_filename)
            counter += 1

        return full_path

    @staticmethod
    async def upload(file: UploadFile):
        archive_ext = (".zip",)

        if file.filename and file.filename.lower().endswith(archive_ext):
            print(f"Загрузка файла {file.filename}")

            full_path = await Uploader.find_path("data/uploaded", file.filename)

            async with aiofiles.open(full_path, "wb") as f:
                while content := await file.read(1024 * 1024):
                    await f.write(content)

            return full_path, Uploader.get_filename(file.filename)

    @staticmethod
    async def save(file: bytes, filename: str, folder: str):
        print(f"Сохранение файла {filename}")

        full_path = await Uploader.find_path(folder, filename + ".zip")

        async with aiofiles.open(full_path, "wb") as f:
            await f.write(file)

        return full_path

    @staticmethod
    async def clear_files(*files):
        await asyncio.gather(*[Uploader.clear_file(file) for file in files])

    @staticmethod
    async def clear_file(file):
        if file and await aos.path.exists(file):
            await aos.remove(file)
            print(f"Удален файл {file}")

    @staticmethod
    async def zip_files(paths: list[str], place="data/tmp", filename=None):
        def write_zip(paths):
            with zipfile.ZipFile(zip_path, "w") as zip_f:
                for path in paths:
                    zip_f.write(path, os.path.basename(path))

        if filename is None:
            filename = f"{str(uuid4())}.zip"

        zip_path = await Uploader.find_path(place, filename)

        await asyncio.to_thread(write_zip, paths)

        return zip_path

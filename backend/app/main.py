import asyncio
from contextlib import asynccontextmanager

import aiofiles.os as aos
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.docs import get_swagger_ui_html

from app.db import create_tables
from app.routing import data_router, processing_router
from app.services import Handler


@asynccontextmanager
async def app_lifespan(app: FastAPI):
    """Жизненный цикл приложения"""
    await check_folders()
    await create_tables()
    await Handler.restart_working_tasks()
    yield
    # await drop_tables()


app = FastAPI(
    lifespan=app_lifespan,
    title="NGW-KPT",
    version="0.1.0",
    docs_url=None,
    redoc_url=None,
)

app.include_router(processing_router, prefix="/processing", tags=["processing"])
app.include_router(data_router, prefix="/data", tags=["data"])

origins = [
    "http://127.0.0.1:8785",
    "http://localhost:8785",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(
        openapi_url=app.openapi_url,
        title=app.title + " - Swagger UI",
        swagger_js_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui-bundle.js",
        swagger_css_url="https://unpkg.com/swagger-ui-dist@5.9.0/swagger-ui.css",
    )


async def check_folders():
    print("Проверка папок")

    folders = [
        "data",
        "data/uploaded",
        "data/results",
        "data/database",
        "data/logs",
        "data/tmp",
    ]

    await asyncio.gather(*[aos.makedirs(folder, exist_ok=True) for folder in folders])

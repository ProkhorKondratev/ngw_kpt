from datetime import datetime
from enum import Enum

from fastapi import File, Form, UploadFile
from pydantic import BaseModel, Field


class ProcessingFormat(Enum):
    geojson = "GeoJSON"
    mapinfo = "MapInfo File"
    shape_file = "ESRI Shapefile"
    gpkg = "GPKG"

    def __str__(self):
        return str(self.value)


class Task(BaseModel):
    id: int
    name: str
    group_id: int
    created_at: datetime
    updated_at: datetime
    status: str
    error: str | None = None

    class Config:
        from_attributes = True


class ProcessingParams(BaseModel):
    files: list[UploadFile] = Field(File(description="Список файлов для обработки"))
    name: str | None = Field(Form(None, description="Название группы"))
    force_add: bool = Field(Form(False, description="Принудительное добавление"))
    format: ProcessingFormat = Field(Form(ProcessingFormat.shape_file, description="Формат результатов"))
    merge_objects: bool = Field(Form(False, description="Объединять объекты одного типа"))
    save_default_crs: bool = Field(Form(True, description="Не трансформировать средствами NextGIS"))
    skip_empty_geom: bool = Field(Form(False, description="Пропускать объекты без геометрии"))
    remove_empty_attrs: bool = Field(Form(False, description="Удалять пустые атрибуты"))
    convert_additional_data: bool = Field(Form(False, description="Конвертировать доп. данные (табличные)"))

    def get_params(self) -> dict:
        return {
            "format": str(self.format),
            "merge_objects": self.merge_objects,
            "save_default_crs": self.save_default_crs,
            "skip_empty_geom": self.skip_empty_geom,
            "remove_empty_attrs": self.remove_empty_attrs,
            "convert_additional_data": self.convert_additional_data,
        }

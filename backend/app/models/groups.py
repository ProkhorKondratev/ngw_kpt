from datetime import datetime

from pydantic import BaseModel


class Group(BaseModel):
    id: int
    name: str
    statistics: dict
    created_at: datetime

    class Config:
        from_attributes = True

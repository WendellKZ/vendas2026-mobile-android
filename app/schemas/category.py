from pydantic import BaseModel

from app.schemas.common import ORMBase


class CategoryCreate(BaseModel):
    name: str


class CategoryRead(ORMBase):
    id: int
    name: str

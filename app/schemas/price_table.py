from pydantic import BaseModel

from app.schemas.common import ORMBase


class PriceTableItemCreate(BaseModel):
    product_id: int
    price: float


class PriceTableCreate(BaseModel):
    company_id: int
    name: str
    is_default: bool = False
    items: list[PriceTableItemCreate] = []


class PriceTableItemRead(ORMBase):
    id: int
    product_id: int
    price: float


class PriceTableRead(ORMBase):
    id: int
    company_id: int
    name: str
    is_default: bool
    items: list[PriceTableItemRead] = []

from pydantic import BaseModel

from app.schemas.common import ORMBase


class StockCreate(BaseModel):
    branch_id: int
    product_id: int
    quantity: float
    reserved_quantity: float = 0


class StockRead(ORMBase):
    id: int
    branch_id: int
    product_id: int
    quantity: float
    reserved_quantity: float

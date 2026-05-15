from pydantic import BaseModel

from app.schemas.common import ORMBase


class PaymentConditionCreate(BaseModel):
    name: str
    installments: int = 1
    interest_percent: float = 0
    entry_percent: float = 0


class PaymentConditionRead(ORMBase):
    id: int
    name: str
    installments: int
    interest_percent: float
    entry_percent: float

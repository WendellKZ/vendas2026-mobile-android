from pydantic import BaseModel


class ProductCreate(BaseModel):
    company_id: int | None = None
    category_id: int | None = None
    code: str | None = None
    sku: str | None = None
    name: str
    category: str | None = None
    unit: str = "UN"
    price_table: float = 0
    price: float | None = None
    price_minimum: float = 0
    min_price: float | None = None
    commission: float = 0
    commission_percent: float | None = None
    stock: float = 0


class ProductRead(ProductCreate):
    id: int

    model_config = {"from_attributes": True}

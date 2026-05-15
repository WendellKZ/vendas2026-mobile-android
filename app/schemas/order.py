from pydantic import BaseModel


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: int = 1
    discount: float = 0
    discount_percent: float | None = None


class OrderCreate(BaseModel):
    company_id: int | None = None
    branch_id: int | None = None
    customer_id: int
    seller_id: int | None = None
    carrier_id: int | None = None
    payment_condition_id: int | None = None
    payment_condition: str | None = None
    delivery_location: str | None = None
    freight_value: float = 0
    items: list[OrderItemCreate]


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    discount: float
    total: float

    model_config = {"from_attributes": True}


class OrderRead(BaseModel):
    id: int
    customer_id: int
    seller_id: int | None = None
    carrier_id: int | None = None
    status: str
    payment_condition: str | None = None
    delivery_location: str | None = None
    freight_value: float
    total_gross: float
    total_discount: float
    total_net: float
    net_total: float
    items: list[OrderItemRead]

    model_config = {"from_attributes": True}

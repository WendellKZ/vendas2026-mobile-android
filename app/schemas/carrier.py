from pydantic import BaseModel, EmailStr


class CarrierCreate(BaseModel):
    name: str
    document: str | None = None
    city: str | None = None
    phone: str | None = None
    email: EmailStr | None = None


class CarrierRead(CarrierCreate):
    id: int

    model_config = {"from_attributes": True}

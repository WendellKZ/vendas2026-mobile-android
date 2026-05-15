from datetime import datetime

from pydantic import BaseModel, EmailStr
class CustomerCreate(BaseModel):
    name: str
    corporate_name: str | None = None
    document: str | None = None
    state_registration: str | None = None
    city: str | None = None
    delivery_location: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    billing_email: EmailStr | None = None
    status: str = "ativo"
    suframa: str | None = None
    suframa_status: str | None = None
    suframa_fonte: str | None = None
    suframa_consultado_em: datetime | None = None
    suframa_modo: str | None = None
class CustomerRead(CustomerCreate):
    id: int
    model_config = {"from_attributes": True}

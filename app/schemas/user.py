from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    role: str = "seller"
    password_hash: str | None = None
    active: bool = True
    company_id: int | None = None
    branch_id: int | None = None


class UserRead(UserCreate):
    id: int

    model_config = {"from_attributes": True}

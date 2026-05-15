from pydantic import BaseModel


class CompanyCreate(BaseModel):
    name: str


class CompanyRead(CompanyCreate):
    id: int

    model_config = {"from_attributes": True}

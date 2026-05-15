from pydantic import BaseModel


class BranchCreate(BaseModel):
    name: str
    company_id: int


class BranchRead(BranchCreate):
    id: int

    model_config = {"from_attributes": True}

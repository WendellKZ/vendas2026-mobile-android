from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.branch import Branch
from app.schemas.branch import BranchCreate, BranchRead

router = APIRouter(prefix="/api/v1/branches", tags=["branches"])


@router.get("/", response_model=list[BranchRead])
def list_branches(db: Session = Depends(get_db)):
    return db.query(Branch).order_by(Branch.id).all()


@router.post("/", response_model=BranchRead, status_code=201)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db)):
    obj = Branch(**payload.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

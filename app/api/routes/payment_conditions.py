from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.payment_condition import PaymentCondition
from app.schemas.payment_condition import PaymentConditionCreate, PaymentConditionRead

router = APIRouter(prefix="/api/v1/payment-conditions", tags=["payment-conditions"])


@router.post("/", response_model=PaymentConditionRead, status_code=201)
def create_payment_condition(payload: PaymentConditionCreate, db: Session = Depends(get_db)):
    condition = PaymentCondition(**payload.model_dump())
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition


@router.get("/", response_model=list[PaymentConditionRead])
def list_payment_conditions(db: Session = Depends(get_db)):
    return db.query(PaymentCondition).all()

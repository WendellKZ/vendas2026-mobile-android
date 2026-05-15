from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockRead

router = APIRouter(prefix="/api/v1/stocks", tags=["stocks"])


@router.post("/", response_model=StockRead, status_code=201)
def create_stock(payload: StockCreate, db: Session = Depends(get_db)):
    stock = Stock(**payload.model_dump())
    db.add(stock)
    db.commit()
    db.refresh(stock)
    return stock


@router.get("/", response_model=list[StockRead])
def list_stocks(db: Session = Depends(get_db)):
    return db.query(Stock).all()

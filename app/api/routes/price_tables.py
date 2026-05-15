from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.models.price_table import PriceTable, PriceTableItem
from app.schemas.price_table import PriceTableCreate, PriceTableRead

router = APIRouter(prefix="/api/v1/price-tables", tags=["price-tables"])


@router.post("/", response_model=PriceTableRead, status_code=201)
def create_price_table(payload: PriceTableCreate, db: Session = Depends(get_db)):
    table = PriceTable(
        company_id=payload.company_id,
        name=payload.name,
        is_default=payload.is_default,
    )
    db.add(table)
    db.flush()

    for item in payload.items:
        db.add(PriceTableItem(price_table_id=table.id, **item.model_dump()))

    db.commit()
    return (
        db.query(PriceTable)
        .options(joinedload(PriceTable.items))
        .filter(PriceTable.id == table.id)
        .first()
    )


@router.get("/", response_model=list[PriceTableRead])
def list_price_tables(db: Session = Depends(get_db)):
    return db.query(PriceTable).options(joinedload(PriceTable.items)).all()

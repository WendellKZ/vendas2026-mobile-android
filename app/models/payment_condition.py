from sqlalchemy import Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PaymentCondition(Base):
    __tablename__ = "payment_conditions"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    installments: Mapped[int] = mapped_column(Integer, default=1)
    interest_percent: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    entry_percent: Mapped[float] = mapped_column(Numeric(10, 2), default=0)


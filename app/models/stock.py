from sqlalchemy import ForeignKey, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Stock(Base):
    __tablename__ = "stocks"

    id: Mapped[int] = mapped_column(primary_key=True)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    reserved_quantity: Mapped[float] = mapped_column(Numeric(10, 2), default=0)

    branch = relationship("Branch", back_populates="stocks")
    product = relationship("Product", back_populates="stocks")

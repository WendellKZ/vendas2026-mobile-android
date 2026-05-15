from sqlalchemy import Boolean, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class PriceTable(Base):
    __tablename__ = "price_tables"

    id: Mapped[int] = mapped_column(primary_key=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)

    company = relationship("Company", back_populates="price_tables")
    items = relationship("PriceTableItem", back_populates="price_table", cascade="all, delete-orphan")


class PriceTableItem(Base):
    __tablename__ = "price_table_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    price_table_id: Mapped[int] = mapped_column(ForeignKey("price_tables.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    price_table = relationship("PriceTable", back_populates="items")
    product = relationship("Product", back_populates="price_table_items")

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym

from app.db.base import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True, index=True)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    category: Mapped[str | None] = mapped_column(String(80), nullable=True)
    unit: Mapped[str] = mapped_column(String(20), default="UN")
    price_table: Mapped[float] = mapped_column(Float, default=0)
    price_minimum: Mapped[float] = mapped_column(Float, default=0)
    commission: Mapped[float] = mapped_column(Float, default=0)
    stock: Mapped[float] = mapped_column(Float, default=0)

    category_obj = relationship("Category", back_populates="products")
    price_table_items = relationship("PriceTableItem", back_populates="product")
    stocks = relationship("Stock", back_populates="product")

    sku = synonym("code")
    price = synonym("price_table")
    min_price = synonym("price_minimum")
    commission_percent = synonym("commission")

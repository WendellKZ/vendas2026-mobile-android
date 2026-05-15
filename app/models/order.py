from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    seller_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    carrier_id: Mapped[int | None] = mapped_column(ForeignKey("carriers.id"), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="em_orcamento")
    payment_condition: Mapped[str | None] = mapped_column(String(80), nullable=True)
    delivery_location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    freight_value: Mapped[float] = mapped_column(Float, default=0)
    total_gross: Mapped[float] = mapped_column(Float, default=0)
    total_discount: Mapped[float] = mapped_column(Float, default=0)
    total_net: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    commission_percent: Mapped[float] = mapped_column(Float, default=0)
    commission_total: Mapped[float] = mapped_column(Float, default=0)
    approval_required_role: Mapped[str | None] = mapped_column(String(30), nullable=True)
    max_discount_applied: Mapped[float] = mapped_column(Float, default=0)
    rule_summary: Mapped[str | None] = mapped_column(String(255), nullable=True)

    customer = relationship("Customer")
    seller = relationship("User")
    carrier = relationship("Carrier")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    @property
    def net_total(self) -> float:
        return float(self.total_net or 0)


class OrderItem(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    discount: Mapped[float] = mapped_column(Float, default=0)
    total: Mapped[float] = mapped_column(Float, default=0)

    order = relationship("Order", back_populates="items")
    product = relationship("Product")

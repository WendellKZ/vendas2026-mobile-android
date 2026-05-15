from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CommercialRule(Base):
    __tablename__ = "commercial_rules"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), index=True)
    rule_type: Mapped[str] = mapped_column(String(30), default="discount")  # discount | commission
    scope: Mapped[str] = mapped_column(String(30), default="global")  # global | customer | product | seller
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[int] = mapped_column(Integer, default=10)
    max_discount_percent: Mapped[float] = mapped_column(Float, default=0)
    approval_limit_manager: Mapped[float] = mapped_column(Float, default=5)
    approval_limit_admin: Mapped[float] = mapped_column(Float, default=10)
    commission_percent: Mapped[float] = mapped_column(Float, default=0)
    commission_high_discount_percent: Mapped[float] = mapped_column(Float, default=0)
    active: Mapped[bool] = mapped_column(Boolean, default=True)

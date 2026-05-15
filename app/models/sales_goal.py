from sqlalchemy import Float, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class SalesGoal(Base):
    __tablename__ = "sales_goals"
    __table_args__ = (UniqueConstraint("seller_id", "year", "month", name="uq_sales_goal_seller_period"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    year: Mapped[int] = mapped_column(Integer, index=True)
    month: Mapped[int] = mapped_column(Integer, index=True)
    goal_value: Mapped[float] = mapped_column(Float, default=0)
    notes: Mapped[str | None] = mapped_column(String(255), nullable=True)

    seller = relationship("User")

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(120))
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"))

    company = relationship("Company")
    stocks = relationship("Stock", back_populates="branch")

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    corporate_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    document: Mapped[str | None] = mapped_column(String(40), nullable=True, index=True)
    state_registration: Mapped[str | None] = mapped_column(String(40), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    suframa: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str | None] = mapped_column(String(30), nullable=True, default="ativa")

    price_tables = relationship("PriceTable", back_populates="company")

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base
class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    company_id: Mapped[int | None] = mapped_column(ForeignKey("companies.id"), nullable=True, index=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    corporate_name: Mapped[str | None] = mapped_column(String(180), nullable=True)
    document: Mapped[str | None] = mapped_column(String(30), nullable=True)
    state_registration: Mapped[str | None] = mapped_column(String(40), nullable=True)
    city: Mapped[str | None] = mapped_column(String(80), nullable=True)
    delivery_location: Mapped[str | None] = mapped_column(String(180), nullable=True)
    email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(40), nullable=True)
    billing_email: Mapped[str | None] = mapped_column(String(150), nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="ativo")
    suframa: Mapped[str | None] = mapped_column(String(30), nullable=True)
    suframa_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    suframa_fonte: Mapped[str | None] = mapped_column(String(50), nullable=True)
    suframa_consultado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    suframa_modo: Mapped[str | None] = mapped_column(String(20), nullable=True)

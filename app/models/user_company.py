from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserCompany(Base):
    __tablename__ = "user_companies"
    __table_args__ = (
        UniqueConstraint("user_id", "company_id", name="uq_user_company"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    company_id: Mapped[int] = mapped_column(ForeignKey("companies.id"), index=True)

    user = relationship("User")
    company = relationship("Company")

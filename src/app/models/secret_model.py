import uuid

from datetime import datetime

from sqlalchemy import ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base

class SecretModel(Base):
    """SQLAlchemy ORM model for OpenLabs Secrets."""

    __tablename__ = "secrets"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, primary_key=True)

    aws_access_key: Mapped[str] = mapped_column(String, nullable=True)
    aws_secret_key: Mapped[str] = mapped_column(String, nullable=True)
    aws_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    azure_client_id: Mapped[str] = mapped_column(String, nullable=True)
    azure_client_secret: Mapped[str] = mapped_column(String, nullable=True)
    azure_created_at: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    user = relationship("UserModel", back_populates="secrets")

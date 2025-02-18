from datetime import datetime

from sqlalchemy import Boolean, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column

from ..core.db.database import Base
from .openlabs_base_model import OpenLabsUserMixin

class OpenLabsUserModel(Base, OpenLabsUserMixin):
    """SQLAlchemy ORM model for User."""

    __tablename__ = "users"

    name: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)

    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    last_active: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    # One-to-one relationship with secrets. 
    # For now, users can only have one azure or one aws secret
    secrets = relationship("OpenLabsSecretModel", back_populates="user", cascade="all, delete-orphan", uselist=False)

from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from .openlabs_base_model import OpenLabsTemplateMixin


class OpenLabsRangeModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for OpenLabsRange."""

    __tablename__ = "ranges"

    provider: Mapped[str] = mapped_column(String, nullable=False)
    vnc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vpn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # One-to-many relationship with VPCs
    vpcs = relationship(
        "OpenLabsVPCModel", back_populates="range", cascade="all, delete-orphan"
    )

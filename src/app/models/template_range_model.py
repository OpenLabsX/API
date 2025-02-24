from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from ..enums.providers import OpenLabsProvider
from .template_base_model import TemplateModelMixin


class TemplateRangeModel(Base, TemplateModelMixin):
    """SQLAlchemy ORM model for template range objects."""

    __tablename__ = "range_templates"

    name: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[OpenLabsProvider] = mapped_column(
        Enum(OpenLabsProvider), nullable=False
    )
    vnc: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    vpn: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # One-to-many relationship with VPCs
    vpcs = relationship(
        "TemplateVPCModel", back_populates="range", cascade="all, delete-orphan"
    )

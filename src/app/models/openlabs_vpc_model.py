import uuid
from ipaddress import IPv4Network

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import CIDR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from .template_base_model import OpenLabsTemplateMixin


class OpenLabsVPCModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for OpenLabsVPC."""

    __tablename__ = "vpcs"

    name: Mapped[str] = mapped_column(String, nullable=False)
    cidr: Mapped[IPv4Network] = mapped_column(CIDR, nullable=False)

    # ForeignKey to ensure each VPC belongs to exactly one Range
    range_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ranges.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
    )

    # Relationship with Range
    range = relationship("OpenLabsRangeModel", back_populates="vpcs")

    # One-to-many relationship with Subnets
    subnets = relationship(
        "OpenLabsSubnetModel", back_populates="vpc", cascade="all, delete-orphan"
    )

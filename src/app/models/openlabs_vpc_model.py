import uuid
from ipaddress import IPv4Network
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CIDR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from .openlabs_base_model import OpenLabsTemplateMixin

if TYPE_CHECKING:
    from src.app.models.openlabs_range_model import OpenLabsRangeModel
    from src.app.models.openlabs_subnet_model import OpenLabsSubnetModel


class OpenLabsVPCModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for OpenLabsVPC."""

    __tablename__ = "vpcs"

    cidr: Mapped[IPv4Network] = mapped_column(CIDR, nullable=False)

    # ForeignKey to ensure each VPC belongs to exactly one Range
    range_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("ranges.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship with Range
    range: Mapped[OpenLabsRangeModel] = relationship(
        "OpenLabsRangeModel", back_populates="vpcs"
    )

    # One-to-many relationship with Subnets
    subnets: Mapped[list[OpenLabsSubnetModel]] = relationship(
        "OpenLabsSubnetModel", back_populates="vpc", cascade="all, delete-orphan"
    )

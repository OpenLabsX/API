import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import CIDR, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from .openlabs_base_model import OpenLabsTemplateMixin


class OpenLabsSubnetModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for OpenLabsSubnet."""

    __tablename__ = "subnets"

    cidr: Mapped[uuid.UUID] = mapped_column(CIDR, nullable=False)

    # ForeignKey to ensure each Subnet belongs to exactly one VPC
    vpc_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("vpcs.id", ondelete="CASCADE"), nullable=False
    )

    # Relationship with VPC
    vpc = relationship("OpenLabsVPCModel", back_populates="subnets")

    # One-to-many relationship with Hosts
    hosts = relationship(
        "OpenLabsHostModel", back_populates="subnet", cascade="all, delete-orphan"
    )

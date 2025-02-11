import uuid

from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from .openlabs_base_model import OpenLabsTemplateMixin


class OpenLabsHostModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for OpenLabsHost."""

    __tablename__ = "hosts"

    hostname: Mapped[str] = mapped_column(String, nullable=False)
    os: Mapped[str] = mapped_column(String, nullable=False)
    spec: Mapped[str] = mapped_column(String, nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default=[], init=False)

    # ForeignKey to ensure each Host belongs to exactly one Subnet
    subnet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subnets.id", ondelete="CASCADE"),
        nullable=False,
        init=False,
    )

    # Relationship with Subnet
    subnet = relationship("OpenLabsSubnetModel", back_populates="hosts")

import uuid

from sqlalchemy import Enum, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.db.database import Base
from ..enums.operating_systems import OpenLabsOS
from ..enums.specs import OpenLabsSpec
from .template_base_model import OpenLabsTemplateMixin


class TemplateHostModel(Base, OpenLabsTemplateMixin):
    """SQLAlchemy ORM model for template host."""

    __tablename__ = "template_hosts"

    hostname: Mapped[str] = mapped_column(String, nullable=False)
    os: Mapped[OpenLabsOS] = mapped_column(Enum(OpenLabsOS), nullable=False)
    spec: Mapped[OpenLabsSpec] = mapped_column(Enum(OpenLabsSpec), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    # Relationship with Subnet
    subnet = relationship("OpenLabsSubnetModel", back_populates="hosts")

    # ForeignKey to ensure each Host belongs to exactly one Subnet
    subnet_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subnets.id", ondelete="CASCADE"),
        nullable=True,
        default=None,
    )

    tags: Mapped[list[str]] = mapped_column(ARRAY(String), default_factory=list)

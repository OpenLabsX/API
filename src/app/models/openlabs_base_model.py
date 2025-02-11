import uuid

from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column


class OpenLabsTemplateMixin:
    """Mixin to provide a UUID for each template-based model."""

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4()
    )
    name: Mapped[str] = mapped_column(String, nullable=False)

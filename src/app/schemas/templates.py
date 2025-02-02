import uuid

from pydantic import BaseModel


class TemplateResponse(BaseModel):
    """Response when templates are stored/saved."""

    id: uuid.UUID

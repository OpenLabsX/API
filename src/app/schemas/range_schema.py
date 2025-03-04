import uuid

from pydantic import BaseModel, ConfigDict, Field

from ..enums.providers import OpenLabsProvider
from ..enums.regions import OpenLabsRegion
from .template_range_schema import TemplateRangeSchema


class RangeBaseSchema(BaseModel):
    """Based schema deployed range object."""

    name: str = Field(
        ..., description="Range name", min_length=1, examples=["live-range-1"]
    )
    template: TemplateRangeSchema = Field(..., description="Range template to deploy")
    provider: OpenLabsProvider = Field(
        ...,
        description="Cloud provider",
        examples=[OpenLabsProvider.AWS, OpenLabsProvider.AZURE],
    )
    region: OpenLabsRegion = Field(
        ...,
        description="Cloud region to deploy range",
        examples=[OpenLabsRegion.US_EAST_1, OpenLabsRegion.US_EAST_2],
    )
    vnc: bool = Field(default=False, description="Has VNC configuration")
    vpn: bool = Field(default=False, description="Has VPN configuration")


class RangeID(BaseModel):
    """Class for range ID."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique object identifier."
    )

    model_config = ConfigDict(from_attributes=True)


class RangeSchema(RangeID, RangeBaseSchema):
    """Deployed range object schema."""

    model_config = ConfigDict(from_attributes=True)

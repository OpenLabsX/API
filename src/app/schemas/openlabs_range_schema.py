import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..enums.providers import OpenLabsProvider
from .openlabs_vpc_schema import OpenLabsVPCBaseSchema


class OpenLabsRangeBaseSchema(BaseModel):
    """Base range object for OpenLabs."""

    vpcs: list[OpenLabsVPCBaseSchema] = Field(..., description="Contained VPCs")
    provider: OpenLabsProvider = Field(
        ...,
        description="Cloud provider",
        examples=[OpenLabsProvider.AWS, OpenLabsProvider.AZURE],
    )

    name: str = Field(
        ..., description="Range name", min_length=1, examples=["example-range-1"]
    )
    vnc: bool = Field(default=False, description="Enable automatic VNC configuration")
    vpn: bool = Field(default=False, description="Enable automatic VPN configuration")

    @field_validator("vpcs")
    @classmethod
    def validate_unique_vpc_names(
        cls, vpcs: list[OpenLabsVPCBaseSchema]
    ) -> list[OpenLabsVPCBaseSchema]:
        """Check VPC names are unique.

        Args:
        ----
            cls: OpenLabsRange object.
            vpcs (list[OpenLabsVPC]): VPC objects.

        Returns:
        -------
            list[OpenLabsVPC]: VPC objects.

        """
        vpc_names = [vpc.name for vpc in vpcs]
        if len(vpc_names) != len(set(vpc_names)):
            msg = "All VPC names must be unique."
            raise (ValueError(msg))
        return vpcs


class OpenLabsRangeID(BaseModel):
    """Identity class for OpenLabsRange."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique range identifier."
    )
    model_config = ConfigDict(from_attributes=True)


class OpenLabsRangeSchema(OpenLabsRangeBaseSchema, OpenLabsRangeID):
    """Range object for OpenLabs."""

    model_config = ConfigDict(from_attributes=True)


class OpenLabsRangeHeaderSchema(OpenLabsRangeID):
    """Header (non-nested object) information for the OpenLabsRangeSchema."""

    provider: OpenLabsProvider = Field(
        ...,
        description="Cloud provider",
        examples=[OpenLabsProvider.AWS, OpenLabsProvider.AZURE],
    )

    name: str = Field(
        ..., description="Range name", min_length=1, examples=["example-range-1"]
    )
    vnc: bool = Field(default=False, description="Enable automatic VNC configuration")
    vpn: bool = Field(default=False, description="Enable automatic VPN configuration")

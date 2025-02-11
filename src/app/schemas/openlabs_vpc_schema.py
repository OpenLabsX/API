import uuid
from ipaddress import IPv4Network

from pydantic import BaseModel, Field, field_validator

from .openlabs_subnet_schema import OpenLabsSubnetBaseSchema


class OpenLabsVPCBaseSchema(BaseModel):
    """VPC object for OpenLabs."""

    cidr: IPv4Network = Field(
        ..., description="CIDR range", examples=["192.168.0.0/16"]
    )
    name: str = Field(
        ..., description="VPC name", min_length=1, examples=["example-vpc-1"]
    )
    subnets: list[OpenLabsSubnetBaseSchema] = Field(
        ..., description="Contained subnets"
    )

    @field_validator("subnets")
    @classmethod
    def validate_unique_subnet_names(
        cls, subnets: list[OpenLabsSubnetBaseSchema]
    ) -> list[OpenLabsSubnetBaseSchema]:
        """Check subnet names are unique.

        Args:
        ----
            cls: OpenLabsVPC object.
            subnets (list[OpenLabsSubnet]): Subnet objects.

        Returns:
        -------
            list[OpenLabsSubnet]: Subnet objects.

        """
        subnet_names = [subnet.name for subnet in subnets]
        if len(subnet_names) != len(set(subnet_names)):
            msg = "All subnet names must be unique."
            raise (ValueError(msg))
        return subnets


class OpenLabsVPCSchema(OpenLabsVPCBaseSchema):
    """VPC object for OpenLabs."""

    id: uuid.UUID = uuid.uuid4()

    class Config:
        """Config options for OpenLabsVPC object."""

        orm_mode = True

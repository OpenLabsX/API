import uuid
from ipaddress import IPv4Network

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

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
            raise ValueError(msg)
        return subnets

    @field_validator("subnets")
    @classmethod
    def validate_subnets_contained(
        cls, subnets: list[OpenLabsSubnetBaseSchema], info: ValidationInfo
    ) -> list[OpenLabsSubnetBaseSchema]:
        """Check that the VPC CIDR contains all subnet CIDRs.

        Args:
        ----
            cls: OpenLabsVPCBaseSchema object.
            subnets (list[OpenLabsSubnetBaseSchema]): Subnet objects.
            info (ValidationInfo): Info of object currently being validated.

        Returns:
        -------
            list[OpenLabsSubnetBaseSchema]: List of subnet objects.

        """
        vpc_cidr = info.data.get("cidr")

        if not vpc_cidr:
            msg = "VPC missing CIDR."
            raise ValueError(msg)

        for subnet in subnets:
            if not subnet.cidr.subnet_of(vpc_cidr):
                msg = f"The following subnet is not contained in the VPC subnet {vpc_cidr}: {subnet.cidr}"
                raise ValueError(msg)

        return subnets


class OpenLabsVPCID(BaseModel):
    """Identity class for OpenLabsVPC."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique VPC identifier."
    )

    model_config = ConfigDict(from_attributes=True)


class OpenLabsVPCSchema(OpenLabsVPCBaseSchema, OpenLabsVPCID):
    """VPC object for OpenLabs."""

    model_config = ConfigDict(from_attributes=True)


class OpenLabsVPCHeaderSchema(OpenLabsVPCID):
    """Header (non-nested object) information for the OpenLabsVPCSchema."""

    cidr: IPv4Network = Field(
        ..., description="CIDR range", examples=["192.168.0.0/16"]
    )
    name: str = Field(
        ..., description="VPC name", min_length=1, examples=["example-vpc-1"]
    )

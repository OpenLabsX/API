import uuid
from ipaddress import IPv4Network

from pydantic import BaseModel, Field, field_validator

from .openlabs_host_schema import OpenLabsHostBaseSchema


class OpenLabsSubnetBaseSchema(BaseModel):
    """Subnet object for OpenLabs."""

    cidr: IPv4Network = Field(
        ..., description="CIDR range", examples=["192.168.1.0/24"]
    )
    name: str = Field(
        ..., description="Subnet name", min_length=1, examples=["example-subnet-1"]
    )
    hosts: list[OpenLabsHostBaseSchema] = Field(..., description="All hosts in subnet")

    @field_validator("hosts")
    @classmethod
    def validate_unique_hostnames(
        cls, hosts: list[OpenLabsHostBaseSchema]
    ) -> list[OpenLabsHostBaseSchema]:
        """Check hostnames are unique.

        Args:
        ----
            cls: OpenLabsSubnet object.
            hosts (list[OpenLabsHost]): Host objects.

        Returns:
        -------
            list[OpenLabsHost]: Host objects.

        """
        hostnames = [host.hostname for host in hosts]
        if len(hostnames) != len(set(hostnames)):
            msg = "All hostnames must be unique."
            raise ValueError(msg)
        return hosts


class OpenLabsSubnetID(BaseModel):
    """Identiy class for OpenLabsSubnet."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique subnet identifier."
    )

    class Config:
        """Config options for OpenLabsSubnetID object."""

        from_attributes = True


class OpenLabsSubnetSchema(OpenLabsSubnetBaseSchema, OpenLabsSubnetID):
    """Subnet object for OpenLabs."""

    class Config:
        """Config options for OpenLabsSubnet object."""

        from_attributes = True

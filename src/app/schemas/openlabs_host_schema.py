import uuid

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationInfo,
    field_validator,
)

from ..enums.operating_systems import OpenLabsOS
from ..enums.specs import OpenLabsSpec
from ..validators.network import is_valid_disk_size, is_valid_hostname


class OpenLabsHostBaseSchema(BaseModel):
    """Base host object for OpenLabs."""

    hostname: str = Field(
        ...,
        description="Hostname of machine",
        min_length=1,
        examples=["example-host-1"],
    )
    os: OpenLabsOS = Field(
        ...,
        description="Operating system of machine",
        examples=[OpenLabsOS.DEBIAN_11, OpenLabsOS.KALI, OpenLabsOS.WINDOWS_2022],
    )
    spec: OpenLabsSpec = Field(
        ...,
        description="Ram and CPU size",
        examples=[OpenLabsSpec.TINY, OpenLabsSpec.SMALL],
    )
    size: int = Field(
        ..., description="Size in GB of disk", gt=0, examples=[8, 32, 40, 65]
    )
    tags: list[str] = Field(
        default_factory=list,
        description="Optional list of tags",
        examples=[["web", "linux"]],
    )

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, tags: list[str]) -> list[str]:
        """Validate no empty tags.

        Args:
        ----
            cls: Host object.
            tags (list[str]): List of tags.

        Returns:
        -------
            list[str]: List of non-empty tags.

        """
        if any(tag.strip() == "" for tag in tags):
            msg = "Tags must not be empty"
            raise ValueError(msg)
        return tags

    @field_validator("hostname")
    @classmethod
    def validate_hostname(cls, hostname: str) -> str:
        """Check VM hostname is conforms to RFC1035.

        Args:
        ----
            cls: Host object.
            hostname (str): Hostname of VM.

        Returns:
        -------
            str: Valid hostname for VM.

        """
        if not is_valid_hostname(hostname):
            msg = f"Invalid hostname: {hostname}"
            raise ValueError(msg)
        return hostname

    @field_validator("size")
    @classmethod
    def validate_size(cls, size: int, info: ValidationInfo) -> int:
        """Check VM disk size is sufficient.

        Args:
        ----
            cls: Host object.
            size (int): Disk size of VM.
            info (ValidationInfo): Validator context

        Returns:
        -------
            int: Valid disk size for VM.

        """
        os: OpenLabsOS | None = info.data.get("os")

        if os is None:
            msg = "OS field not set to OpenLabsOS type."
            raise ValueError(msg)

        if not is_valid_disk_size(os, size):
            msg = f"Invalid disk size for {os.value}: {size}GB"
            raise ValueError(msg)
        return size


class OpenLabsHostID(BaseModel):
    """Identity class for OpenLabsHost."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique object identifier."
    )

    model_config = ConfigDict(from_attributes=True)


class OpenLabsHostSchema(OpenLabsHostBaseSchema, OpenLabsHostID):
    """Host object for OpenLabs."""

    model_config = ConfigDict(from_attributes=True)

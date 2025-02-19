from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

class OpenLabsSecretBaseSchema(BaseModel):
    """Base secret object for OpenLabs."""

    aws_access_key: str | None = Field(
        default=None,
        description="Access key for AWS account",
    )
    aws_secret_key: str | None = Field(
        default=None,
        description="Secret key for AWS account",
    )

    aws_created_at: datetime | None = Field(
        default=None,
        description="Time AWS secrets were populated",
        examples=[datetime(2025, 2, 5)]
    )

    azure_client_id: str | None = Field(
        default=None,
        description="Client ID for Azure",
    )

    azure_client_secret: str | None = Field(
        default=None,
        description="Client secret for Azure",
    )

    azure_created_at: datetime | None = Field(
        default=None,
        description="Time Azure secrets were populated",
        examples=[datetime(2025, 2, 5)]
    )

class OpenLabsSecretSchema(OpenLabsSecretBaseSchema):
    """Secret object for OpenLabs."""

    model_config = ConfigDict(from_attributes=True)

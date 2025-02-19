from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict

class OpenLabsSecretSchema(BaseModel):
    """Base secret object for OpenLabs."""

    aws_access_key: str = Field(
        description="Access key for AWS account",
    )
    aws_secret_key: str = Field(
        description="Secret key for AWS account",
    )

    aws_created_at: datetime = Field(
        description="Time AWS secrets were populated",
        examples=[datetime(2025, 2, 5)]
    )

    azure_client_id: str = Field(
        description="Client ID for Azure",
    )

    azure_client_secret: str = Field(
        description="Client secret for Azure",
    )

    azure_created_at: datetime = Field(
        description="Time Azure secrets were populated",
        examples=[datetime(2025, 2, 5)]
    )

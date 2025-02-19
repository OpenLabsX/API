import uuid
from datetime import datetime

from pydantic import BaseModel, Field, field_validator, ConfigDict
from email_validator import validate_email, EmailNotValidError

from .openlabs_secret_schema import OpenLabsSecretSchema

class OpenLabsUserBaseSchema(BaseModel):
    """Base user object for OpenLabs."""

    name: str = Field(
        ...,
        description="Full name of user",
        min_length=1,
        examples=["Adam Hassan", "Alex Christy", "Naresh Panchal"]
    )
    email: str = Field(
        ...,
        description="Email of user",
        min_length=1,
        examples=["adam@ufsit.club", "alex@christy.com", "naresh@panch.al"],
    )

    #is_admin: bool = Field(default=False, description = "Is this user an admin of OpenLabs?")
    password: str = Field(
        ...,
        description = "Password of user",
        min_length = 1,
        examples=["password123"]
    )
    #hashed_password: str = Field(
    #    ...,
    #    description = "Bcrypt hash of user password",
    #    min_length = 1,
    #    examples=["$2y$10$x4QEI5RQdlbWSKQr8ZuL4.1OIdIdhfuwXJJPtf4/LJXt7mH6HQCsW"],
    #)

    #created_at: datetime = Field(
    #    ...,
    #    description = "Time the user was created",
    #    examples=[datetime(1988, 11, 6)]
    #)

    #last_active: datetime = Field(
    #    ...,
    #    description = "Time the user last made a request",
    #    examples=[datetime(2025, 2, 5)]
    #)

    secrets: OpenLabsSecretSchema = Field(
        default_factory = OpenLabsSecretSchema,
        description = "Secrets used for providers",
    )

    @field_validator("email")
    @classmethod
    def validate_email(
        cls, email: str) -> str:
        """Check that email format is valid.

        Args:
        ----
            cls: OpenLabsUser object.
            email (str): User email address.

        Returns:
        -------
            str: User email address.
        """

        try:
            # Makes a DNS query to validate deliverability
            # We do this, as users will only be added to DB on registration
            emailinfo = validate_email(email, check_deliverability=True)

            return emailinfo.normalized
        except EmailNotValidError:
            msg = "Provided email address is invalid."
            raise ValueError(msg)


class OpenLabsUserID(BaseModel):
    """Identity class for OpenLabsUser."""

    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique user identifier."
    )

    model_config = ConfigDict(from_attributes=True)


class OpenLabsUserSchema(OpenLabsUserBaseSchema, OpenLabsUserID):
    """User object for OpenLabs."""

    model_config = ConfigDict(from_attributes=True)

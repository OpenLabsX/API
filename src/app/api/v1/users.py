from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_users import create_user
from ...crud.crud_secrets import create_secret

from ...schemas.openlabs_user_schema import (
    OpenLabsUserBaseSchema,
    OpenLabsUserID,
    OpenLabsUserSchema,
)
from ...schemas.openlabs_secret_schema import (
    OpenLabsSecretBaseSchema,
    OpenLabsSecretSchema,
)

router = APIRouter(prefix="/register", tags=["register"])

@router.post("/")
async def register_new_user(
    openlabs_user: OpenLabsUserBaseSchema,
    db: AsyncSession = Depends(async_get_db), # noqa: B008
) -> OpenLabsUserID:
    """Create a new user.

    Args:
    ----
        openlabs_user (OpenLabsUserBaseSchema): OpenLabs compliance user object.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsUserID: Identity of the user template.
    """

    created_user = await create_user(db, openlabs_user)

    if not created_user:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unable to create user",
        )

    return OpenLabsUserID.model_validate(created_user, from_attributes=True)

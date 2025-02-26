from datetime import UTC, datetime

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from ...crud.crud_users import get_user_by_id
from ...models.user_model import UserModel
from ...schemas.user_schema import UserID
from ..config import settings
from ..db.database import async_get_db

# Create a security scheme using HTTPBearer
security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security), # noqa: B008
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> UserModel:
    """Get the current user from the JWT token.

    Args:
    ----
        credentials (HTTPAuthorizationCredentials): HTTP Bearer token
        db (AsyncSession): Database connection

    Returns:
    -------
        UserModel: The current authenticated user

    Raises:
    ------
        HTTPException: If the token is invalid or the user doesn't exist

    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            credentials.credentials,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        # Get the user ID from the token
        user_id = payload.get("user")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get the expiration time from the token
        expiration = payload.get("exp")
        if expiration is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has no expiration",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if the token has expired
        if datetime.now(UTC) > datetime.fromtimestamp(expiration, tz=UTC):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get the user from the database
        user = await get_user_by_id(db, UserID(id=user_id))
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Update the last_active field - remove timezone to match DB schema
        now = datetime.now(UTC)
        user.last_active = now.replace(tzinfo=None)
        await db.commit()

        return user

    except jwt.PyJWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def is_admin(user: UserModel = Depends(get_current_user) # noqa: B008
             ) -> UserModel:
    """Check if the user is an admin.

    Args:
    ----
        user (UserModel): The authenticated user

    Returns:
    -------
        UserModel: The authenticated user if they are an admin

    Raises:
    ------
        HTTPException: If the user is not an admin

    """
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions",
        )
    return user

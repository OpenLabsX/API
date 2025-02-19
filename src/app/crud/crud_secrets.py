from sqlalchemy.ext.asyncio.session import AsyncSession
from ..models.openlabs_secret_model import OpenLabsSecretModel
from ..schemas.openlabs_secret_schema import OpenLabsSecretBaseSchema, OpenLabsSecretSchema
from ..schemas.openlabs_user_schema import OpenLabsUserID

async def create_secret(
    db: AsyncSession,
    openlabs_secret: OpenLabsSecretBaseSchema,
    user_id: OpenLabsUserID) -> OpenLabsSecretModel:
    """Create and add a new OpenLabsSecret to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_secret (OpenLabsSecretBaseSchema): Dictionary containing OpenLabsUser data.
        user_id (OpenLabsUserID): User ID.

    Returns:
    -------
        OpenLabsSecret: The newly created secret.

    """
    openlabs_secret = OpenLabsSecretSchema(**openlabs_secret.model_dump())
    secret_dict = openlabs_secret.model_dump()
    if user_id:
        secret_dict["user_id"] = user_id.id

    secret_obj = OpenLabsSecretModel(**secret_dict)
    db.add(secret_obj)

    await db.commit()

    # TODO: idk what this is for
    await db.refresh(secret_obj)

    return secret_obj

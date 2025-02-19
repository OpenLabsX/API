from sqlalchemy.ext.asyncio.session import AsyncSession
from ..models.openlabs_secret_model import OpenLabsSecretModel

async def create_secret(
    db: AsyncSession,
    openlabs_secret: OpenLabsSecretBaseSchema) -> OpenLabsSecretModel:
    """Create and add a new OpenLabsSecret to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_secret (OpenLabsSecretBaseSchema): Dictionary containing OpenLabsUser data.

    Returns:
    -------
        OpenLabsSecret: The newly created secret.

    """
    openlabs_secret = OpenLabsSecretSchema(**openlabs_secret.model_dump())
    secret_dict = openlabs_secret.model_dump()

    secret_obj = OpenLabsSecretModel(**secret_dict)
    db.add(secret_obj)

    await db.commit()
    db.refresh(secret_obj)

    return secret_obj

from sqlalchemy.ext.asyncio.session import AsyncSession
from ..models.openlabs_user_model import OpenLabsUserModel
from ..schemas.openlabs_user_schema import OpenLabsUserBaseSchema, OpenLabsUserID, OpenLabsUserSchema
from ..crud.crud_secrets import create_secret
from datetime import datetime

from bcrypt import gensalt, hashpw

async def create_user(db: AsyncSession, openlabs_user: OpenLabsUserBaseSchema) -> OpenLabsUserModel:
    """Create and add a new OpenLabsUser to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_user (OpenLabsBaseUserSchema): Dictionary containing OpenLabsUser data.

    Returns:
    -------
        OpenLabsUser: The newly created user.

    """

    openlabs_user = OpenLabsUserSchema(**openlabs_user.model_dump())
    user_dict = openlabs_user.model_dump(exclude={"secrets"})

    # Here, we populate fields to match the database model
    del user_dict["password"]

    hash_salt = gensalt()
    hashed_password = hashpw(openlabs_user.password.encode(), hash_salt)

    user_dict["hashed_password"] = hashed_password.decode()

    user_dict["created_at"] = datetime.now()
    user_dict["last_active"] = datetime.now()

    user_dict["is_admin"] = False

    user_obj = OpenLabsUserModel(**user_dict)
    db.add(user_obj)

    user_id = OpenLabsUserID(id=user_obj.id)

    secrets_object = await create_secret(db, openlabs_user.secrets, user_id)

    db.add(secrets_object)

    await db.commit()

    return user_obj

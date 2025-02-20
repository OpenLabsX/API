from sqlalchemy.ext.asyncio.session import AsyncSession
from ..models.openlabs_user_model import OpenLabsUserModel
from ..models.openlabs_secret_model import OpenLabsSecretModel
from ..schemas.openlabs_user_schema import OpenLabsUserBaseSchema, OpenLabsUserID, OpenLabsUserSchema
from ..schemas.openlabs_secret_schema import OpenLabsSecretSchema
from ..crud.crud_secrets import create_secret
from datetime import datetime

from sqlalchemy import select, inspect
from sqlalchemy.orm import load_only

from bcrypt import gensalt, hashpw


async def get_user(db: AsyncSession, email: str) -> OpenLabsUserModel:
    """Get a user by email.
    
    Args:
    ----
        db (Session): Database connection.
        email (str): User email.
        
    Returns:
    -------
        OpenLabsUser: The user.
    """

    mapped_user_model = inspect(OpenLabsUserModel)
    main_columns = [
        getattr(OpenLabsUserModel, attr.key)
        for attr in mapped_user_model.column_attrs
    ]

    stmt = (
        select(OpenLabsUserModel)
        .where(OpenLabsUserModel.email == email)
        .options(load_only(*main_columns))
    )

    result = await db.execute(stmt)

    return result.scalars().first()


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

    empty_secret = OpenLabsSecretSchema()

    secrets_object = await create_secret(db, empty_secret, user_id)

    db.add(secrets_object)

    await db.commit()

    return user_obj

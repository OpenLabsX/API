from datetime import UTC, datetime
import uuid

from bcrypt import gensalt, hashpw
from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import load_only

from ..models.secret_model import SecretModel
from ..models.user_model import UserModel
from ..schemas.secret_schema import SecretSchema
from ..schemas.user_schema import (
    UserCreateBaseSchema,
    UserCreateSchema,
    UserID,
)


async def create_secret(
    db: AsyncSession, secret: SecretSchema, user_id: UserID
) -> SecretModel:
    """Create a new secret.

    Args:
    ----
        db (AsyncSession): Database connection.
        secret (SecretSchema): Secret data.
        user_id (UserID): ID of the user who owns this secret.

    Returns:
    -------
        SecretModel: The created secret.

    """
    secret_dict = secret.model_dump()
    secret_dict["user_id"] = user_id.id

    secret_obj = SecretModel(**secret_dict)
    db.add(secret_obj)

    return secret_obj


async def get_user(db: AsyncSession, email: str) -> UserModel | None:
    """Get a user by email.

    Args:
    ----
        db (Session): Database connection.
        email (str): User email.

    Returns:
    -------
        User: The user.

    """
    mapped_user_model = inspect(UserModel)
    main_columns = [
        getattr(UserModel, attr.key) for attr in mapped_user_model.column_attrs
    ]

    stmt = (
        select(UserModel)
        .where(UserModel.email == email)
        .options(load_only(*main_columns))
    )

    result = await db.execute(stmt)

    return result.scalars().first()


async def get_user_by_id(db: AsyncSession, user_id: UserID) -> UserModel | None:
    """Get a user by ID.

    Args:
    ----
        db (Session): Database connection.
        user_id (UserID): User ID.

    Returns:
    -------
        User: The user.

    """
    mapped_user_model = inspect(UserModel)
    main_columns = [
        getattr(UserModel, attr.key) for attr in mapped_user_model.column_attrs
    ]

    stmt = (
        select(UserModel)
        .where(UserModel.id == user_id.id)
        .options(load_only(*main_columns))
    )

    result = await db.execute(stmt)

    return result.scalars().first()


async def create_user(
    db: AsyncSession, openlabs_user: UserCreateBaseSchema, is_admin: bool = False
) -> UserModel:
    """Create and add a new OpenLabsUser to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_user (UserBaseSchema): Dictionary containing User data.
        is_admin (bool): Whether the user should be an admin. Defaults to False.

    Returns:
    -------
        User: The newly created user.

    """
    openlabs_user = UserCreateSchema(**openlabs_user.model_dump())
    user_dict = openlabs_user.model_dump(exclude={"secrets"})

    # Here, we populate fields to match the database model
    del user_dict["password"]

    hash_salt = gensalt()
    hashed_password = hashpw(openlabs_user.password.encode(), hash_salt)

    user_dict["hashed_password"] = hashed_password.decode()

    user_dict["created_at"] = datetime.now(UTC)
    user_dict["last_active"] = datetime.now(UTC)

    user_dict["is_admin"] = is_admin

    user_obj = UserModel(**user_dict)
    db.add(user_obj)

    user_id = UserID(id=user_obj.id)

    empty_secret = SecretSchema()

    secrets_object = await create_secret(db, empty_secret, user_id)

    db.add(secrets_object)

    await db.commit()

    return user_obj


async def create_admin_user(
    db: AsyncSession, email: str, password: str, name: str
) -> UserModel:
    """Create an admin user if one with the provided email doesn't exist.

    Args:
    ----
        db (Session): Database connection.
        email (str): Admin email.
        password (str): Admin password.
        name (str): Admin name.

    Returns:
    -------
        UserModel: The created admin user or existing user.
    """
    # Check if admin user already exists
    existing_user = await get_user(db, email)
    
    if existing_user:
        # If the user exists but is not an admin, make them an admin
        if not existing_user.is_admin:
            existing_user.is_admin = True
            await db.commit()
        return existing_user
    
    try:
        # Create the user using the ORM
        now = datetime.now(UTC)
        user_id = uuid.uuid4()
        
        # Hash the password
        hash_salt = gensalt()
        hashed_password = hashpw(password.encode(), hash_salt).decode()
        
        # Create the user model directly
        stmt = UserModel.__table__.insert().values(
            id=user_id,
            name=name,
            email=email,
            hashed_password=hashed_password,
            created_at=now,
            last_active=now,
            is_admin=True
        )
        
        await db.execute(stmt)
        
        # Create the secret model directly
        stmt = SecretModel.__table__.insert().values(user_id=user_id)
        await db.execute(stmt)
        
        await db.commit()
        
        # Get the created user
        user_obj = await get_user_by_id(db, UserID(id=user_id))
        return user_obj
        
    except Exception as e:
        await db.rollback()
        raise ValueError(f"Error creating admin user: {str(e)}") from e

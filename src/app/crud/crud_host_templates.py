import logging

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only

from ..models.template_host_model import TemplateHostModel
from ..schemas.template_host_schema import (
    TemplateHostBaseSchema,
    TemplateHostID,
    TemplateHostSchema,
)
from ..schemas.template_subnet_schema import TemplateSubnetID

logger = logging.getLogger(__name__)


async def get_host_template_headers(
    db: AsyncSession, standalone_only: bool = True
) -> list[TemplateHostModel]:
    """Get list of host template headers.

    Args:
    ----
        db (Session): Database connection.
        standalone_only (bool): Include only hosts that are standalone templates
            (i.e. those with a null subnet_id). Defaults to True.

    Returns:
    -------
        list[TemplateHostModel]: List of host template models.

    """
    mapped_host_model = inspect(TemplateHostModel)
    main_columns = [
        getattr(TemplateHostModel, attr.key) for attr in mapped_host_model.column_attrs
    ]

    # Build the query: filter for rows where subnet_id is null if standalone_only is True
    if standalone_only:
        stmt = (
            select(TemplateHostModel)
            .where(TemplateHostModel.subnet_id.is_(None))
            .options(load_only(*main_columns))
        )
    else:
        stmt = select(TemplateHostModel).options(load_only(*main_columns))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_host_template(
    db: AsyncSession, host_id: TemplateHostID
) -> TemplateHostModel | None:
    """Get host template by ID.

    Args:
    ----
        db (Sessions): Database connection.
        host_id (TemplateHostID): ID of the host.

    Returns:
    -------
        Optional[TemplateHostModel]: TemplateHostModel if it exists.

    """
    stmt = select(TemplateHostModel).filter(TemplateHostModel.id == host_id.id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_host_template(
    db: AsyncSession,
    template_host: TemplateHostBaseSchema,
    subnet_id: TemplateSubnetID | None = None,
) -> TemplateHostModel:
    """Create and add a new host tempalte to the database.

    Args:
    ----
        db (Session): Database connection.
        template_host (TemplateHostBaseSchema): Dictionary containing host data.
        subnet_id (Optional[str]): Subnet ID to link VPC back too.

    Returns:
    -------
        TemplateHostModel: The newly created template host.

    """
    template_host = TemplateHostSchema(**template_host.model_dump())
    host_dict = template_host.model_dump()
    if subnet_id:
        host_dict["subnet_id"] = subnet_id.id

    host_obj = TemplateHostModel(**host_dict)
    db.add(host_obj)

    if not subnet_id:
        await db.commit()
        await db.refresh(host_obj)

    return host_obj


async def delete_host_template(db: AsyncSession, host_model: TemplateHostModel) -> bool:
    """Delete a standalone host template.

    Only allows deletion if the host template is standalone (i.e. subnet_id is None).

    Args:
    ----
        db (Sessions): Database connection.
        host_model (TemplateHostModel): Host template model object.

    Returns:
    -------
        bool: True if successfully delete. False otherwise.

    """
    if not host_model.is_standalone():
        log_msg = "Cannot delete host template because it is not a standalone template."
        logger.error(log_msg)
        return False

    await db.delete(host_model)
    await db.commit()
    return True

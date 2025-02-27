import logging

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from ..models.template_subnet_model import TemplateSubnetModel
from ..models.template_vpc_model import TemplateVPCModel
from ..schemas.template_range_schema import TemplateRangeID
from ..schemas.template_vpc_schema import (
    TemplateVPCBaseSchema,
    TemplateVPCID,
    TemplateVPCSchema,
)
from .crud_subnet_templates import create_subnet_template

logger = logging.getLogger(__name__)


async def get_vpc_template_headers(
    db: AsyncSession, standalone_only: bool = True
) -> list[TemplateVPCModel]:
    """Get list of VPC template headers.

    Args:
    ----
        db (AsyncSession): Database connection.
        standalone_only (bool): Include only VPCs that are standalone templates
            (i.e. those with a null range_id). Defaults to True.

    Returns:
    -------
        list[TemplateVPCModel]: List of VPC template models.

    """
    # Dynamically select non-nested columns/attributes
    mapped_vpc_model = inspect(TemplateVPCModel)
    main_columns = [
        getattr(TemplateVPCModel, attr.key) for attr in mapped_vpc_model.column_attrs
    ]

    # Build the query: filter for rows where range_id is null if standalone_only is True
    if standalone_only:
        stmt = (
            select(TemplateVPCModel)
            .where(TemplateVPCModel.range_id.is_(None))
            .options(load_only(*main_columns))
        )
    else:
        stmt = select(TemplateVPCModel).options(load_only(*main_columns))

    # Execute query and return results
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_vpc_template(
    db: AsyncSession, vpc_id: TemplateVPCID
) -> TemplateVPCModel | None:
    """Get VPC template by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        vpc_id (TemplateVPCID): ID of the range.

    Returns:
    -------
        Optional[OpenLabsVPC]: TemplateVPCModel if it exists in database.

    """
    stmt = (
        select(TemplateVPCModel)
        .options(
            selectinload(TemplateVPCModel.subnets).selectinload(
                TemplateSubnetModel.hosts
            )
        )
        .filter(TemplateVPCModel.id == vpc_id.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_vpc_template(
    db: AsyncSession,
    vpc_template: TemplateVPCBaseSchema,
    range_id: TemplateRangeID | None = None,
) -> TemplateVPCModel:
    """Create and add a new VPC template to the database.

    Args:
    ----
        db (Session): Database connection.
        vpc_template (TemplateVPCBaseSchema): Dictionary containing OpenLabsVPC data.
        range_id (Optional[str]): Range ID to link VPC back too.

    Returns:
    -------
        OpenLabsVPC: The newly created VPC.

    """
    vpc_template = TemplateVPCSchema(**vpc_template.model_dump())
    vpc_dict = vpc_template.model_dump(exclude={"subnets"})
    if range_id:
        vpc_dict["range_id"] = range_id.id

    vpc_obj = TemplateVPCModel(**vpc_dict)
    db.add(vpc_obj)

    # Add subnets
    subnet_objects = [
        await create_subnet_template(db, subnet_data, TemplateVPCID(id=vpc_obj.id))
        for subnet_data in vpc_template.subnets
    ]

    # Commit if we are parent
    if range_id:
        db.add_all(subnet_objects)
    else:
        await db.commit()
        await db.refresh(vpc_obj)

    return vpc_obj


async def delete_vpc_template(db: AsyncSession, vpc_model: TemplateVPCModel) -> bool:
    """Delete a standalone subnet template.

    Only allows deletion if the subnet template is standalone (i.e. vpc_id is None).

    Args:
    ----
        db (Sessions): Database connection.
        vpc_model (TemplateVPCModel): Subnet template model object.

    Returns:
    -------
        bool: True if successfully delete. False otherwise.

    """
    if not vpc_model.is_standalone():
        log_msg = "Cannot delete VPC template because it is not a standalone template."
        logger.error(log_msg)

        return False

    await db.delete(vpc_model)
    await db.commit()
    return True

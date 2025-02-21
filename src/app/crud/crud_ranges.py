from sqlalchemy import inspect
from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from ..models.template_range_model import TemplateRangeModel
from ..models.template_subnet_model import TemplateSubnetModel
from ..models.template_vpc_model import TemplateVPCModel
from ..schemas.template_range_schema import (
    TemplateRangeBaseSchema,
    TemplateRangeID,
    TemplateRangeSchema,
)
from .crud_vpcs import create_vpc


async def get_range_headers(db: AsyncSession) -> list[TemplateRangeModel]:
    """Get list of OpenLabsRange headers.

    Args:
    ----
        db (Session): Database connection.

    Returns:
    -------
        list[TemplateRangeModel]: List of TemplateRangeModel objects.

    """
    # Dynamically select non-nested columns/attributes
    mapped_range_model = inspect(TemplateRangeModel)
    main_columns = [
        getattr(TemplateRangeModel, attr.key)
        for attr in mapped_range_model.column_attrs
    ]

    stmt = select(TemplateRangeModel).options(load_only(*main_columns))
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_range(
    db: AsyncSession, range_id: TemplateRangeID
) -> TemplateRangeModel | None:
    """Get OpenLabsRange by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        range_id (TemplateRangeID): ID of the range.

    Returns:
    -------
        Optional[OpenLabsRange]: OpenLabsRange if it exists in database.

    """
    # Eagerly fetch relationships to make single query
    stmt = (
        select(TemplateRangeModel)
        .options(
            selectinload(TemplateRangeModel.vpcs)
            .selectinload(TemplateVPCModel.subnets)
            .selectinload(TemplateSubnetModel.hosts)
        )
        .filter(TemplateRangeModel.id == range_id.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_range(
    db: AsyncSession, openlabs_range: TemplateRangeBaseSchema
) -> TemplateRangeModel:
    """Create and add a new OpenLabsRange to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_range (TemplateRangeSchema): Dictionary containing OpenLabsRange data.

    Returns:
    -------
        OpenLabsRange: The newly created range.

    """
    openlabs_range = TemplateRangeSchema(**openlabs_range.model_dump())
    range_dict = openlabs_range.model_dump(exclude={"vpcs"})

    # Create the Range object (No commit yet)
    range_obj = TemplateRangeModel(**range_dict)
    db.add(range_obj)  # Stage the range

    # Build range ID
    range_id = TemplateRangeID(id=range_obj.id)

    # Create VPCs and associate them with the range (No commit yet)
    vpc_objects = [
        await create_vpc(db, vpc_data, range_id) for vpc_data in openlabs_range.vpcs
    ]
    # range_obj.vpcs = vpc_objects
    db.add_all(vpc_objects)  # Stage VPCs

    # Commit everything in one transaction
    await db.commit()

    return range_obj

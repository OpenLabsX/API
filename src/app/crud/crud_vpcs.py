from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..models.openlabs_vpc_model import OpenLabsVPCModel
from ..schemas.template_range_schema import OpenLabsRangeID
from ..schemas.template_vpc_schema import (
    TemplateVPCBaseSchema,
    TemplateVPCID,
    TemplateVPCSchema,
)
from .crud_subnets import create_subnet


async def get_vpc_headers(
    db: AsyncSession, standalone_only: bool = True
) -> list[OpenLabsVPCModel]:
    """Get list of OpenLabsVPC headers.

    Args:
    ----
        db (AsyncSession): Database connection.
        standalone_only (bool): Include only VPCs that are standalone templates
            (i.e. those with a null range_id). Defaults to True.

    Returns:
    -------
        list[OpenLabsVPCModel]: List of OpenLabsVPC models.

    """
    # Dynamically select non-nested columns/attributes
    mapped_vpc_model = inspect(OpenLabsVPCModel)
    main_columns = [
        getattr(OpenLabsVPCModel, attr.key) for attr in mapped_vpc_model.column_attrs
    ]

    # Build the query: filter for rows where range_id is null if standalone_only is True
    if standalone_only:
        stmt = (
            select(OpenLabsVPCModel)
            .where(OpenLabsVPCModel.range_id.is_(None))
            .options(load_only(*main_columns))
        )
    else:
        stmt = select(OpenLabsVPCModel).options(load_only(*main_columns))

    # Execute query and return results
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_vpc(db: AsyncSession, vpc_id: TemplateVPCID) -> OpenLabsVPCModel | None:
    """Get OpenLabsVPC by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        vpc_id (TemplateVPCID): ID of the range.

    Returns:
    -------
        Optional[OpenLabsVPC]: OpenLabsVPCModel if it exists in database.

    """
    stmt = (
        select(OpenLabsVPCModel)
        .options(
            selectinload(OpenLabsVPCModel.subnets).selectinload(
                OpenLabsSubnetModel.hosts
            )
        )
        .filter(OpenLabsVPCModel.id == vpc_id.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_vpc(
    db: AsyncSession,
    openlabs_vpc: TemplateVPCBaseSchema,
    range_id: OpenLabsRangeID | None = None,
) -> OpenLabsVPCModel:
    """Create and add a new OpenLabsVPC to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_vpc (TemplateVPCBaseSchema): Dictionary containing OpenLabsVPC data.
        range_id (Optional[str]): Range ID to link VPC back too.

    Returns:
    -------
        OpenLabsVPC: The newly created VPC.

    """
    openlabs_vpc = TemplateVPCSchema(**openlabs_vpc.model_dump())
    vpc_dict = openlabs_vpc.model_dump(exclude={"subnets"})
    if range_id:
        vpc_dict["range_id"] = range_id.id

    vpc_obj = OpenLabsVPCModel(**vpc_dict)
    db.add(vpc_obj)

    # Add subnets
    subnet_objects = [
        await create_subnet(db, subnet_data, TemplateVPCID(id=vpc_obj.id))
        for subnet_data in openlabs_vpc.subnets
    ]

    # Commit if we are parent
    if range_id:
        db.add_all(subnet_objects)
    else:
        await db.commit()
        await db.refresh(vpc_obj)

    return vpc_obj

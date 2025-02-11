from sqlalchemy.ext.asyncio.session import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.openlabs_range_model import OpenLabsRangeModel
from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..models.openlabs_vpc_model import OpenLabsVPCModel
from ..schemas.openlabs_range_schema import OpenLabsRangeBaseSchema, OpenLabsRangeSchema
from .crud_vpcs import create_vpc


async def get_range(db: AsyncSession, range_id: str) -> OpenLabsRangeModel | None:
    """Get OpenLabsRange by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        range_id (str): UUID of the range.

    Returns:
    -------
        Optional[OpenLabsRange]: OpenLabsRange if it exists in database.

    """
    # Eagerly fetch relationships to make single query
    stmt = (
        select(OpenLabsRangeModel)
        .options(
            selectinload(OpenLabsRangeModel.vpcs)
            .selectinload(OpenLabsVPCModel.subnets)
            .selectinload(OpenLabsSubnetModel.hosts)
        )
        .filter(OpenLabsRangeModel.id == range_id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_range(
    db: AsyncSession, openlabs_range: OpenLabsRangeBaseSchema
) -> OpenLabsRangeModel:
    """Create and add a new OpenLabsRange to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_range (OpenLabsRangeSchema): Dictionary containing OpenLabsRange data.

    Returns:
    -------
        OpenLabsRange: The newly created range.

    """
    openlabs_range = OpenLabsRangeSchema(**openlabs_range.model_dump())
    range_dict = openlabs_range.model_dump(exclude={"vpcs"})

    # Create the Range object (No commit yet)
    range_obj = OpenLabsRangeModel(**range_dict)
    db.add(range_obj)  # Stage the range

    # Create VPCs and associate them with the range (No commit yet)
    vpc_objects = [
        await create_vpc(db, vpc_data, str(range_obj.id))
        for vpc_data in openlabs_range.vpcs
    ]
    # range_obj.vpcs = vpc_objects
    db.add_all(vpc_objects)  # Stage VPCs

    # Commit everything in one transaction
    await db.commit()
    await db.refresh(range_obj)

    return range_obj

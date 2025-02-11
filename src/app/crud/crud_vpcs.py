from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..models.openlabs_vpc_model import OpenLabsVPCModel
from ..schemas.openlabs_range_schema import OpenLabsRangeID
from ..schemas.openlabs_vpc_schema import (
    OpenLabsVPCBaseSchema,
    OpenLabsVPCID,
    OpenLabsVPCSchema,
)
from .crud_subnets import create_subnet


async def get_vpc(db: AsyncSession, vpc_id: OpenLabsVPCID) -> OpenLabsVPCModel | None:
    """Get OpenLabsVPC by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        vpc_id (OpenLabsVPCID): ID of the range.

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
    openlabs_vpc: OpenLabsVPCBaseSchema,
    range_id: OpenLabsRangeID | None = None,
) -> OpenLabsVPCModel:
    """Create and add a new OpenLabsVPC to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_vpc (OpenLabsVPCBaseSchema): Dictionary containing OpenLabsVPC data.
        range_id (Optional[str]): Range ID to link VPC back too.

    Returns:
    -------
        OpenLabsVPC: The newly created VPC.

    """
    openlabs_vpc = OpenLabsVPCSchema(**openlabs_vpc.model_dump())
    vpc_dict = openlabs_vpc.model_dump(exclude={"subnets"})
    if range_id:
        vpc_dict["range_id"] = range_id.id

    vpc_obj = OpenLabsVPCModel(**vpc_dict)
    db.add(vpc_obj)

    # Add subnets
    subnet_objects = [
        await create_subnet(db, subnet_data, str(vpc_obj.id))
        for subnet_data in openlabs_vpc.subnets
    ]

    # Commit if we are parent
    if range_id:
        db.add_all(subnet_objects)
    else:
        await db.commit()
        await db.refresh(vpc_obj)

    return vpc_obj

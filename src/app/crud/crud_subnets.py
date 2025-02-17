from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..schemas.openlabs_subnet_schema import (
    OpenLabsSubnetBaseSchema,
    OpenLabsSubnetID,
    OpenLabsSubnetSchema,
)
from ..schemas.openlabs_vpc_schema import OpenLabsVPCID
from .crud_hosts import create_host


async def get_subnets(db: AsyncSession) -> list[OpenLabsSubnetID]:
    """Get list of OpenLabsSubnet uuids.

    Args:
    ----
        db (Session): Database connection.

    Returns:
    -------
        list[OpenLabsSubnetID]: List of all OpenLabsSubnetID for each OpenSubnetVPC.

    """
    stmt = select(OpenLabsSubnetModel.id)
    result = await db.execute(stmt)
    return [OpenLabsSubnetID(id=subnet_id) for subnet_id in result.scalars().all()]


async def get_subnet(
    db: AsyncSession, subnet_id: OpenLabsSubnetID
) -> OpenLabsSubnetModel | None:
    """Get OpenLabsSubnet by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        subnet_id (OpenLabsSubnetID): UUID of the VPC.

    Returns:
    -------
        Optional[OpenLabsSubnet]: OpenLabsSubnetModel if it exists in database.

    """
    stmt = (
        select(OpenLabsSubnetModel)
        .options(selectinload(OpenLabsSubnetModel.hosts))
        .filter(OpenLabsSubnetModel.id == subnet_id.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_subnet(
    db: AsyncSession,
    openlabs_subnet: OpenLabsSubnetBaseSchema,
    vpc_id: OpenLabsVPCID | None = None,
) -> OpenLabsSubnetModel:
    """Create and add a new OpenLabsSubnet to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_subnet (OpenLabsSubnetBaseSchema): Dictionary containing OpenLabsSubnet data.
        vpc_id (Optional[OpenLabsVPCID]): VPC ID to link subnet back too.

    Returns:
    -------
        OpenLabsSubnet: The newly created Subnet.

    """
    openlabs_subnet = OpenLabsSubnetSchema(**openlabs_subnet.model_dump())
    subnet_dict = openlabs_subnet.model_dump(exclude={"hosts"})
    if vpc_id:
        subnet_dict["vpc_id"] = vpc_id.id

    subnet_obj = OpenLabsSubnetModel(**subnet_dict)
    db.add(subnet_obj)

    # Add subnets
    host_objects = [
        await create_host(db, host_data, OpenLabsSubnetID(id=subnet_obj.id))
        for host_data in openlabs_subnet.hosts
    ]

    # Commit if we are parent object
    if vpc_id:
        db.add_all(host_objects)
    else:
        await db.commit()
        await db.refresh(subnet_obj)

    return subnet_obj

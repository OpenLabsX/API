from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from ..models.openlabs_host_model import OpenLabsHostModel
from ..schemas.openlabs_host_schema import (
    OpenLabsHostBaseSchema,
    OpenLabsHostID,
    OpenLabsHostSchema,
)
from ..schemas.openlabs_subnet_schema import OpenLabsSubnetID


async def get_host(
    db: AsyncSession, host_id: OpenLabsHostID
) -> OpenLabsHostModel | None:
    """Get OpenLabs host by ID.

    Args:
    ----
        db (Sessions): Database connection.
        host_id (OpenLabsHostID): ID of the host.

    Returns:
    -------
        Optional[OpenLabsHostModel]: OpenLabsHostModel if it exists.

    """
    stmt = select(OpenLabsHostModel).filter(OpenLabsHostModel.id == host_id.id)
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_host(
    db: AsyncSession,
    openlabs_host: OpenLabsHostBaseSchema,
    subnet_id: OpenLabsSubnetID | None = None,
) -> OpenLabsHostModel:
    """Create and add a new OpenLabsHost to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_host (OpenLabsHostBaseSchema): Dictionary containing OpenLabsHost data.
        subnet_id (Optional[str]): Subnet ID to link VPC back too.

    Returns:
    -------
        OpenLabsVPC: The newly created range.

    """
    openlabs_host = OpenLabsHostSchema(**openlabs_host.model_dump())
    host_dict = openlabs_host.model_dump()
    if subnet_id:
        host_dict["subnet_id"] = subnet_id.id

    host_obj = OpenLabsHostModel(**host_dict)
    db.add(host_obj)

    if not subnet_id:
        await db.commit()
        await db.refresh(host_obj)

    return host_obj

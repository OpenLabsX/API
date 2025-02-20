from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..schemas.template_subnet_schema import (
    TemplateSubnetBaseSchema,
    TemplateSubnetID,
    TemplateSubnetSchema,
)
from ..schemas.template_vpc_schema import TemplateVPCID
from .crud_hosts import create_host


async def get_subnet_headers(
    db: AsyncSession, standalone_only: bool = True
) -> list[OpenLabsSubnetModel]:
    """Get list of OpenLabsSubnet headers.

    Args:
    ----
        db (Session): Database connection.
        standalone_only (bool): Include only subnets that are standalone templates
            (i.e. those with a null vpc_id). Defaults to True.

    Returns:
    -------
        list[OpenLabsSubnetModel]: List of OpenLabsSubnet models.

    """
    # Dynamically select non-nested columns/attributes
    mapped_subnet_model = inspect(OpenLabsSubnetModel)
    main_columns = [
        getattr(OpenLabsSubnetModel, attr.key)
        for attr in mapped_subnet_model.column_attrs
    ]

    # Build the query: filter for rows where vpc_id is null if standalone_only is True
    if standalone_only:
        stmt = (
            select(OpenLabsSubnetModel)
            .where(OpenLabsSubnetModel.vpc_id.is_(None))
            .options(load_only(*main_columns))
        )
    else:
        stmt = select(OpenLabsSubnetModel).options(load_only(*main_columns))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_subnet(
    db: AsyncSession, subnet_id: TemplateSubnetID
) -> OpenLabsSubnetModel | None:
    """Get OpenLabsSubnet by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        subnet_id (TemplateSubnetID): UUID of the VPC.

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
    openlabs_subnet: TemplateSubnetBaseSchema,
    vpc_id: TemplateVPCID | None = None,
) -> OpenLabsSubnetModel:
    """Create and add a new OpenLabsSubnet to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_subnet (TemplateSubnetBaseSchema): Dictionary containing OpenLabsSubnet data.
        vpc_id (Optional[TemplateVPCID]): VPC ID to link subnet back too.

    Returns:
    -------
        OpenLabsSubnet: The newly created Subnet.

    """
    openlabs_subnet = TemplateSubnetSchema(**openlabs_subnet.model_dump())
    subnet_dict = openlabs_subnet.model_dump(exclude={"hosts"})
    if vpc_id:
        subnet_dict["vpc_id"] = vpc_id.id

    subnet_obj = OpenLabsSubnetModel(**subnet_dict)
    db.add(subnet_obj)

    # Add subnets
    host_objects = [
        await create_host(db, host_data, TemplateSubnetID(id=subnet_obj.id))
        for host_data in openlabs_subnet.hosts
    ]

    # Commit if we are parent object
    if vpc_id:
        db.add_all(host_objects)
    else:
        await db.commit()
        await db.refresh(subnet_obj)

    return subnet_obj

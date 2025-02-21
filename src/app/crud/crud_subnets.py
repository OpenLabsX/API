from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import load_only, selectinload

from ..models.template_subnet_model import TemplateSubnetModel
from ..schemas.template_subnet_schema import (
    TemplateSubnetBaseSchema,
    TemplateSubnetID,
    TemplateSubnetSchema,
)
from ..schemas.template_vpc_schema import TemplateVPCID
from .crud_host_templates import create_host_template


async def get_subnet_headers(
    db: AsyncSession, standalone_only: bool = True
) -> list[TemplateSubnetModel]:
    """Get list of OpenLabsSubnet headers.

    Args:
    ----
        db (Session): Database connection.
        standalone_only (bool): Include only subnets that are standalone templates
            (i.e. those with a null vpc_id). Defaults to True.

    Returns:
    -------
        list[TemplateSubnetModel]: List of OpenLabsSubnet models.

    """
    # Dynamically select non-nested columns/attributes
    mapped_subnet_model = inspect(TemplateSubnetModel)
    main_columns = [
        getattr(TemplateSubnetModel, attr.key)
        for attr in mapped_subnet_model.column_attrs
    ]

    # Build the query: filter for rows where vpc_id is null if standalone_only is True
    if standalone_only:
        stmt = (
            select(TemplateSubnetModel)
            .where(TemplateSubnetModel.vpc_id.is_(None))
            .options(load_only(*main_columns))
        )
    else:
        stmt = select(TemplateSubnetModel).options(load_only(*main_columns))

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def get_subnet(
    db: AsyncSession, subnet_id: TemplateSubnetID
) -> TemplateSubnetModel | None:
    """Get OpenLabsSubnet by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        subnet_id (TemplateSubnetID): UUID of the VPC.

    Returns:
    -------
        Optional[OpenLabsSubnet]: TemplateSubnetModel if it exists in database.

    """
    stmt = (
        select(TemplateSubnetModel)
        .options(selectinload(TemplateSubnetModel.hosts))
        .filter(TemplateSubnetModel.id == subnet_id.id)
    )
    result = await db.execute(stmt)
    return result.scalar_one_or_none()


async def create_subnet(
    db: AsyncSession,
    openlabs_subnet: TemplateSubnetBaseSchema,
    vpc_id: TemplateVPCID | None = None,
) -> TemplateSubnetModel:
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

    subnet_obj = TemplateSubnetModel(**subnet_dict)
    db.add(subnet_obj)

    # Add subnets
    host_objects = [
        await create_host_template(db, host_data, TemplateSubnetID(id=subnet_obj.id))
        for host_data in openlabs_subnet.hosts
    ]

    # Commit if we are parent object
    if vpc_id:
        db.add_all(host_objects)
    else:
        await db.commit()
        await db.refresh(subnet_obj)

    return subnet_obj

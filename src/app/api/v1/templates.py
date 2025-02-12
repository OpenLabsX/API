from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_hosts import create_host, get_host
from ...crud.crud_ranges import create_range, get_range
from ...crud.crud_subnets import create_subnet, get_subnet
from ...crud.crud_vpcs import create_vpc, get_vpc
from ...schemas.openlabs_host_schema import (
    OpenLabsHostBaseSchema,
    OpenLabsHostID,
    OpenLabsHostSchema,
)
from ...schemas.openlabs_range_schema import (
    OpenLabsRangeBaseSchema,
    OpenLabsRangeID,
    OpenLabsRangeSchema,
)
from ...schemas.openlabs_subnet_schema import (
    OpenLabsSubnetBaseSchema,
    OpenLabsSubnetID,
    OpenLabsSubnetSchema,
)
from ...schemas.openlabs_vpc_schema import (
    OpenLabsVPCBaseSchema,
    OpenLabsVPCID,
    OpenLabsVPCSchema,
)
from ...validators.network import max_num_hosts_in_subnet

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/ranges/{range_id}")
async def get_range_template(
    range_id: str, db: AsyncSession = Depends(async_get_db)  # noqa: B008
) -> OpenLabsRangeSchema:
    """Get a range template.

    Args:
    ----
        range_id (str): ID of the range.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsRangeSchema: Range data from database.

    """
    openlabs_range = await get_range(db, OpenLabsRangeID(id=range_id))

    if not openlabs_range:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Range with id: {range_id} not found!",
        )

    return OpenLabsRangeSchema.model_validate(openlabs_range, from_attributes=True)


@router.post("/ranges")
async def upload_range_template(
    openlabs_range: OpenLabsRangeBaseSchema,
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> OpenLabsRangeID:
    """Upload a range template.

    Args:
    ----
        openlabs_range (OpenLabsRangeBaseSchema): OpenLabs compliant range object.
        db (AsynSession): Async database connection.

    Returns:
    -------
        OpenLabsRangeID: Identity of the range template.

    """
    for vpc in openlabs_range.vpcs:
        for subnet in vpc.subnets:
            if not subnet.cidr.subnet_of(vpc.cidr):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"The following subnet is not contained in the VPC subnet {vpc.cidr}: {subnet.cidr}",
                )

    created_range = await create_range(db, openlabs_range)
    return OpenLabsRangeID.model_validate(created_range, from_attributes=True)


@router.get("/vpcs/{vpc_id}")
async def get_vpc_template(
    vpc_id: str, db: AsyncSession = Depends(async_get_db)  # noqa: B008
) -> OpenLabsVPCSchema:
    """Get a VPC template.

    Args:
    ----
        vpc_id (str): ID of the VPC.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsVPCSchema: VPC data from database.

    """
    openlabs_vpc = await get_vpc(db, OpenLabsVPCID(id=vpc_id))

    if not openlabs_vpc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"VPC with id: {vpc_id} not found!",
        )

    return OpenLabsVPCSchema.model_validate(openlabs_vpc, from_attributes=True)


@router.post("/vpcs")
async def upload_vpc_template(
    openlabs_vpc: OpenLabsVPCBaseSchema,
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> OpenLabsVPCID:
    """Upload a VPC template.

    Args:
    ----
        openlabs_vpc (OpenLabsVPCBaseSchema): OpenLabs compliant VPC object.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsVPCID: Identity of the VPC template.

    """
    for subnet in openlabs_vpc.subnets:
        if not subnet.cidr.subnet_of(openlabs_vpc.cidr):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"The following subnet is not contained in the VPC subnet {openlabs_vpc.cidr}: {subnet.cidr}",
            )

    created_vpc = await create_vpc(db, openlabs_vpc)
    return OpenLabsVPCID.model_validate(created_vpc, from_attributes=True)


@router.get("/subnets/{subnet_id}")
async def get_subnet_template(
    subnet_id: str, db: AsyncSession = Depends(async_get_db)  # noqa: B008
) -> OpenLabsSubnetSchema:
    """Get a subnet template.

    Args:
    ----
        subnet_id (str): ID of the subnet.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsSubnetSchema: Subnet data from database.

    """
    openlabs_subnet = await get_subnet(db, OpenLabsSubnetID(id=subnet_id))

    if not openlabs_subnet:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subnet with id: {subnet_id} not found!",
        )

    return OpenLabsSubnetSchema.model_validate(openlabs_subnet, from_attributes=True)


@router.post("/subnets")
async def upload_subnet_template(
    openlabs_subnet: OpenLabsSubnetBaseSchema,
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> OpenLabsSubnetID:
    """Upload a subnet template.

    Args:
    ----
        openlabs_subnet (OpenLabsSubnetBaseSchema): OpenLabs compliant subnet object.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsSubnetID: Identity of the subnet template.

    """
    created_subnet = await create_subnet(db, openlabs_subnet)

    max_hosts = max_num_hosts_in_subnet(openlabs_subnet.cidr)
    num_requested_hosts = len(openlabs_subnet.hosts)
    if num_requested_hosts > max_hosts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Too many hosts in subnet! Max: {max_hosts}, Requested: {num_requested_hosts}",
        )

    return OpenLabsSubnetID.model_validate(created_subnet, from_attributes=True)


@router.get("/hosts/{host_id}")
async def get_host_template(
    host_id: str, db: AsyncSession = Depends(async_get_db)  # noqa: B008
) -> OpenLabsHostSchema:
    """Get a host template.

    Args:
    ----
        host_id (str): Id of the host.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsHostSchema: Host data from database.

    """
    openlabs_host = await get_host(db, OpenLabsHostID(id=host_id))

    if not openlabs_host:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Host with id: {host_id} not found!",
        )

    return OpenLabsHostSchema.model_validate(openlabs_host, from_attributes=True)


@router.post("/hosts")
async def upload_host_template(
    openlabs_host: OpenLabsHostBaseSchema,
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> OpenLabsHostID:
    """Upload a host template.

    Args:
    ----
        openlabs_host (OpenLabsHostBaseSchema): OpenLabs compliant host object.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsHostID: Identity of the subnet template.

    """
    created_host = await create_host(db, openlabs_host)
    return OpenLabsHostSchema.model_validate(created_host, from_attributes=True)

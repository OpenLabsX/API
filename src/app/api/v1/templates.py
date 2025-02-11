from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_ranges import create_range, get_range
from ...crud.crud_vpcs import create_vpc, get_vpc
from ...schemas.openlabs_range_schema import (
    OpenLabsRangeBaseSchema,
    OpenLabsRangeID,
    OpenLabsRangeSchema,
)
from ...schemas.openlabs_vpc_schema import (
    OpenLabsVPCBaseSchema,
    OpenLabsVPCID,
    OpenLabsVPCSchema,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/ranges/{range_id}", tags=["ranges"])
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


@router.post("/ranges", tags=["ranges"])
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


@router.get("/vpcs/{vpc_id}", tags=["vpcs"])
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


@router.post("/vpcs", tags=["vpcs"])
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

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.db.database import async_get_db
from ...crud.crud_ranges import create_range, get_range
from ...models.openlabs_range_model import OpenLabsRangeModel
from ...schemas.openlabs_range_schema import (
    OpenLabsRangeBaseSchema,
)

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("/ranges/{range_id}")
async def get_range_template(
    range_id: uuid.UUID, db: AsyncSession = Depends(async_get_db)  # noqa: B008
) -> OpenLabsRangeModel:
    """Get a range template.

    Args:
    ----
        range_id (uuid.UUID): ID of the range.
        db (AsyncSession): Async database connection.

    Returns:
    -------
        OpenLabsRangeSchema: Range data from database.

    """
    openlabs_range = await get_range(db, str(range_id))

    if not openlabs_range:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Range with id: {range_id} not found!",
        )

    return openlabs_range


@router.post("/ranges")
async def upload_range_template(
    openlabs_range: OpenLabsRangeBaseSchema,
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> OpenLabsRangeModel:
    """Upload a range template.

    Args:
    ----
        openlabs_range (OpenLabsRange): OpenLabs compliant range object.
        db (AsynSession): Async database connection.

    Returns:
    -------
        TemplateResponse: UUID of the range template.

    """
    # # Validate inputted subnets
    # invalid_subnets: list[str] = []
    # for subnet in openlabs_range.vpc.subnets:
    #     if not subnet.cidr.subnet_of(openlabs_range.vpc.cidr):
    #         invalid_subnets.append(str(subnet.cidr))

    # if invalid_subnets:
    #     raise HTTPException(
    #         status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
    #         detail=f"The following subnets are not contained in the VPC subnet {cyber_range.vpc.cidr}: {', '.join(invalid_subnets)}",
    #     )

    return await create_range(db, openlabs_range)

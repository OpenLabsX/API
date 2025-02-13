from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.cdktf.aws.aws import create_aws_stack, deploy_infrastructure
from ...core.config import settings
from ...core.db.database import async_get_db
from ...crud.crud_ranges import get_range
from ...schemas.openlabs_range_schema import OpenLabsRangeID, OpenLabsRangeSchema

router = APIRouter(prefix="/ranges", tags=["templates"])


@router.post("/deploy")
async def deploy_range_template(
    range_ids: list[OpenLabsRangeID], db: AsyncSession = Depends(async_get_db)
) -> dict[str, Any]:
    """Deploy range templates."""
    ranges: list[OpenLabsRangeSchema] = []
    for range_id in range_ids:
        range_model = await get_range(db, range_id)
        ranges.append(
            OpenLabsRangeSchema.model_validate(range_model, from_attributes=True)
        )

    for deploy_range in ranges:
        stack_name = create_aws_stack(deploy_range, settings.CDKTF_DIR)
        deploy_infrastructure(settings.CDKTF_DIR, stack_name)

    return {"deployed": True}

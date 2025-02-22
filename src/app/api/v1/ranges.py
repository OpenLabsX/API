import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...crud.crud_range_templates import get_range_template
from ...schemas.template_range_schema import TemplateRangeID, TemplateRangeSchema

router = APIRouter(prefix="/ranges", tags=["ranges"])


@router.post("/deploy")
async def deploy_range_from_template(
    range_ids: list[TemplateRangeID],
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
) -> dict[str, Any]:
    """Deploy range templates."""
    # Import CDKTF dependencies to avoid long import times
    from ...core.cdktf.aws.aws import create_aws_stack, deploy_infrastructure

    ranges: list[TemplateRangeSchema] = []
    for range_id in range_ids:
        range_model = await get_range_template(db, range_id)
        ranges.append(
            TemplateRangeSchema.model_validate(range_model, from_attributes=True)
        )

    for deploy_range in ranges:
        deployed_range_id = uuid.uuid4()
        stack_name = create_aws_stack(
            deploy_range, settings.CDKTF_DIR, deployed_range_id
        )
        state_file = deploy_infrastructure(settings.CDKTF_DIR, stack_name)

        if not state_file:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to read terraform state file.",
            )
        # deployed_range_obj = DeployedRange(deployed_range_id, range_template, state_file, range_template.provider, account: OpenLabsAccount, cloud_account_id: uuid/int) OpenLabsAccount --> Provider --> Cloud Account ID --> AWS Creds
        # save(db, deployed_range_obj)

    return {"deployed": True}

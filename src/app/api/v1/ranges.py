import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from ...core.config import settings
from ...core.db.database import async_get_db
from ...core.auth.auth import get_current_user
from ...models.user_model import UserModel
from ...crud.crud_range_templates import get_range_template, is_range_template_owner
from ...schemas.template_range_schema import TemplateRangeID, TemplateRangeSchema

router = APIRouter(prefix="/ranges", tags=["ranges"])


@router.post("/deploy")
async def deploy_range_from_template(
    range_ids: list[TemplateRangeID],
    db: AsyncSession = Depends(async_get_db),  # noqa: B008
    current_user: UserModel = Depends(get_current_user),
) -> dict[str, Any]:
    """Deploy range templates.
    
    Args:
    ----
        range_ids (list[TemplateRangeID]): List of range template IDs to deploy.
        db (AsyncSession): Async database connection.
        current_user (UserModel): Currently authenticated user.
        
    Returns:
    -------
        dict[str, Any]: Deployment status.
    """
    # Import CDKTF dependencies to avoid long import times
    from ...core.cdktf.aws.aws import create_aws_stack, deploy_infrastructure

    ranges: list[TemplateRangeSchema] = []
    for range_id in range_ids:
        # Check if the user owns this template
        is_owner = await is_range_template_owner(db, range_id, current_user.id)
        if not is_owner:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"You don't have permission to deploy range with ID: {range_id.id}",
            )
        
        # Get the template
        range_model = await get_range_template(db, range_id, user_id=current_user.id), 
        if not range_model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Range template with ID: {range_id.id} not found or you don't have access to it!",
            )
            
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

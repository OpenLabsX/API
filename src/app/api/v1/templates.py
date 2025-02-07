import uuid

from fastapi import APIRouter, HTTPException, status

from ...core.cdktf.aws.main import create_aws_stack
from ...schemas.openlabs import OpenLabsRange
from ...schemas.templates import TemplateResponse

router = APIRouter(prefix="/templates")


@router.post("/range", tags=["templates"])
async def upload_template(cyber_range: OpenLabsRange) -> TemplateResponse:
    """Upload a range template.

    Args:
    ----
        cyber_range (OpenLabsRange): OpenLabs compliant range object.

    Returns:
    -------
        TemplateResponse: UUID of the range template.

    """
    # Validate inputted subnets
    invalid_subnets: list[str] = []
    for subnet in cyber_range.vpc.subnets:
        if not subnet.cidr.subnet_of(cyber_range.vpc.cidr):
            invalid_subnets.append(str(subnet.cidr))

    if invalid_subnets:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"The following subnets are not contained in the VPC subnet {cyber_range.vpc.cidr}: {', '.join(invalid_subnets)}",
        )

    stack_dir = create_aws_stack(cyber_range)  # Function that takes in cyber range object, creates the aws stack, and deploys it. WIll need to then send it to the database to store

    return TemplateResponse(id=uuid.uuid4())

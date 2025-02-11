from sqlalchemy.orm import Session

from ..models.openlabs_subnet_model import OpenLabsSubnetModel
from ..schemas.openlabs_subnet_schema import (
    OpenLabsSubnetBaseSchema,
    OpenLabsSubnetSchema,
)
from .crud_hosts import create_host


def get_subnet(db: Session, subnet_id: str) -> OpenLabsSubnetModel | None:
    """Get OpenLabsSubnet by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        subnet_id (str): UUID of the VPC.

    Returns:
    -------
        Optional[OpenLabsSubnet]: OpenLabsSubnetModel if it exists in database.

    """
    return (
        db.query(OpenLabsSubnetModel)
        .filter(OpenLabsSubnetModel.id == subnet_id)
        .first()
    )


def create_subnet(
    db: Session, openlabs_subnet: OpenLabsSubnetBaseSchema, vpc_id: str | None = None
) -> OpenLabsSubnetModel:
    """Create and add a new OpenLabsSubnet to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_subnet (OpenLabsSubnetBaseSchema): Dictionary containing OpenLabsSubnet data.
        vpc_id (Optional[str]): VPC ID to link Subnet back too.

    Returns:
    -------
        OpenLabsSubnet: The newly created Subnet.

    """
    openlabs_subnet = OpenLabsSubnetSchema(**openlabs_subnet.model_dump())
    subnet_dict = openlabs_subnet.model_dump(exclude={"hosts"})
    if vpc_id:
        subnet_dict["vpc_id"] = vpc_id

    subnet_obj = OpenLabsSubnetModel(**subnet_dict)
    db.add(subnet_obj)

    # Add subnets
    subnet_objects = [
        create_host(db, subnet_data, str(subnet_obj.id))
        for subnet_data in openlabs_subnet.hosts
    ]

    # Commit if we are parent object
    if vpc_id:
        db.add_all(subnet_objects)
    else:
        db.commit()
        db.refresh(subnet_obj)

    return subnet_obj

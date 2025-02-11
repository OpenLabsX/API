from sqlalchemy.orm import Session

from ..models.openlabs_vpc_model import OpenLabsVPCModel
from ..schemas.openlabs_vpc_schema import OpenLabsVPCBaseSchema, OpenLabsVPCSchema
from .crud_subnets import create_subnet


def get_vpc(db: Session, vpc_id: str) -> OpenLabsVPCModel | None:
    """Get OpenLabsVPC by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        vpc_id (str): UUID of the range.

    Returns:
    -------
        Optional[OpenLabsVPC]: OpenLabsVPCModel if it exists in database.

    """
    return db.query(OpenLabsVPCModel).filter(OpenLabsVPCModel.id == vpc_id).first()


def create_vpc(
    db: Session, openlabs_vpc: OpenLabsVPCBaseSchema, range_id: str | None = None
) -> OpenLabsVPCModel:
    """Create and add a new OpenLabsVPC to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_vpc (OpenLabsVPCBaseSchema): Dictionary containing OpenLabsVPC data.
        range_id (Optional[str]): Range ID to link VPC back too.

    Returns:
    -------
        OpenLabsVPC: The newly created VPC.

    """
    openlabs_vpc = OpenLabsVPCSchema(**openlabs_vpc.model_dump())
    vpc_dict = openlabs_vpc.model_dump(exclude={"subnets"})
    if range_id:
        vpc_dict["range_id"] = range_id

    vpc_obj = OpenLabsVPCModel(**vpc_dict)
    db.add(vpc_obj)

    # Add subnets
    subnet_objects = [
        create_subnet(db, subnet_data, str(vpc_obj.id))
        for subnet_data in openlabs_vpc.subnets
    ]

    # Commit if we are parent
    if range_id:
        db.add_all(subnet_objects)
    else:
        db.commit()
        db.refresh(vpc_obj)

    return vpc_obj

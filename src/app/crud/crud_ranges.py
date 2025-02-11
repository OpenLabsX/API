from sqlalchemy.orm import Session

from ..models.openlabs_range_model import OpenLabsRangeModel
from ..schemas.openlabs_range_schema import OpenLabsRangeBaseSchema


def get_range(db: Session, range_id: str) -> OpenLabsRangeModel | None:
    """Get OpenLabsRange by id (uuid).

    Args:
    ----
        db (Session): Database connection.
        range_id (str): UUID of the range.

    Returns:
    -------
        Optional[OpenLabsRange]: OpenLabsRange if it exists in database.

    """
    return (
        db.query(OpenLabsRangeModel).filter(OpenLabsRangeModel.id == range_id).first()
    )


def create_range(
    db: Session, openlabs_range: OpenLabsRangeBaseSchema
) -> OpenLabsRangeModel:
    """Create and add a new OpenLabsRange to the database.

    Args:
    ----
        db (Session): Database connection.
        openlabs_range (OpenLabsRangeBaseSchema): Dictionary containing OpenLabsRange data.

    Returns:
    -------
        OpenLabsRange: The newly created range.

    """
    db_range = OpenLabsRangeModel(**openlabs_range)
    db.add(db_range)
    db.commit()
    db.refresh(db_range)
    return db_range

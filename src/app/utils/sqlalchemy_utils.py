from typing import Any

from ..core.db.database import Base


def sqlalchemy_model_to_dict(instance: Base, seen: set[int]) -> dict[str, Any]:
    """Convert a single SQLAlchemy ORM instance (inheriting from `Base`) into a dictionary while avoiding recursion.

    Args:
    ----
        instance (Base): A single SQLAlchemy ORM model instance.
        seen (set[int], optional): A set of object IDs to track processed objects (prevents infinite recursion).

    Returns:
    -------
        dict[str, Any]: A dictionary representation of the model instance.

    """
    obj_id = id(instance)  # Unique ID for the SQLAlchemy object

    if obj_id in seen:
        return {"id": getattr(instance, "id", None)}

    seen.add(obj_id)  # Mark this object as seen

    if not isinstance(instance, Base):  # ✅ Ensure only `Base` models are processed
        msg = f"Expected a SQLAlchemy ORM model of type `Base`, got {type(instance).__name__}"
        raise ValueError(msg)

    # Convert columns to a dictionary
    instance_dict: dict[str, Any] = {
        column.name: getattr(instance, column.name)
        for column in instance.__table__.columns
    }

    # Convert relationships recursively
    for relationship in instance.__mapper__.relationships:
        related_obj = getattr(instance, relationship.key)
        if related_obj is not None:
            if isinstance(related_obj, list):
                instance_dict[relationship.key] = [
                    sqlalchemy_model_to_dict(item, seen) for item in related_obj
                ]
            else:
                instance_dict[relationship.key] = sqlalchemy_model_to_dict(
                    related_obj, seen
                )

    return instance_dict


def sqlalchemy_to_pydantic(
    instance: Base | list[Base],
) -> dict[str, Any] | list[dict[str, Any]]:
    """Recursively convert a SQLAlchemy ORM model (or a list of models) into a dictionary compatible with Pydantic model validation.

    Args:
    ----
        instance (Base | list[Base]): A single SQLAlchemy ORM instance or a list of instances.

    Returns:
    -------
        dict[str, Any] | list[dict[str, Any]]: A dictionary (or list of dictionaries) that can be passed to `model_validate()`.

    """
    seen: set[int] = set()  # ✅ Track visited objects across recursion

    if isinstance(instance, list):
        return [sqlalchemy_model_to_dict(item, seen) for item in instance]

    return sqlalchemy_model_to_dict(instance, seen)

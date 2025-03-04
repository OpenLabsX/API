import logging
import uuid
from typing import Any, Dict, Type

from ....enums.providers import OpenLabsProvider
from ....validators.enums import is_valid_enum_value
from .aws_range import AWSRange
from .base_range import CdktfBaseRange

# from .azure_range import AzureRange
# from .gcp_range import GCPRange

# Configure logging
logger = logging.getLogger(__name__)


class RangeFactory:
    """Create range objects."""

    _registry: Dict[OpenLabsProvider, Type[CdktfBaseRange]]

    def __init__(self) -> None:
        """Initialize range factory class."""
        _registry = {
            OpenLabsProvider.AWS: AWSRange,
        }

    # TODO: Create range object for database that will be accepted from
    # @classmethod
    # def create_range(cls, data: dict[str, Any]) -> CdktfBaseRange:
    #     """Create and return a CdktfBaseRange subclass instance based on `data`.

    #     Assumes `data` has a "provider" key which is used to pick
    #     the correct subclass from _registry. The rest of the data is
    #     unpacked as constructor arguments.

    #     Example of `data`:
    #         {
    #             "provider": "AWS",
    #             "id": "6f28cbbc-138c-4be0-bd58-ddb033bb078f",
    #             "template": <TemplateRangeSchema>,
    #             "region": <OpenLabsRegion>,
    #             "owner_id": <UserID>,
    #             ...
    #         }

    #     Note:
    #     ----
    #     This example code assumes each subclass of CdktfBaseRange
    #     accepts the same __init__ signature. If your subclasses
    #     differ, you'll have to adapt or handle arguments more precisely.

    #     Returns:
    #     -------
    #         CdktfBaseRange: A new instance of the appropriate provider subclass.

    #     """
    #     provider = data.get("provider")
    #     if not provider:
    #         msg = "No 'provider' specified in data; cannot create range."
    #         raise ValueError(msg)

    #     if not is_valid_enum_value(OpenLabsProvider, provider, strict=True):
    #         msg = f"Provider: {provider} is not a valid or supported provider."
    #         raise ValueError(msg)

    #     # Get the appropriate range class from the registry
    #     provider = OpenLabsProvider(provider)
    #     range_cls = cls._registry.get(provider)

    #     if not range_cls:
    #         msg = "Failed to determine CDKTF class when instantiating range object."
    #         raise ValueError(msg)

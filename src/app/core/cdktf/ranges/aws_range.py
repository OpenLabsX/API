from ..stacks.aws_stack import AWSStack
from .base_range import CdktfBaseRange


class AWSRange(CdktfBaseRange):
    """Range deployed to AWS."""

    def get_provider_stack_class(self) -> type[AWSStack]:
        """Return AWSStack class."""
        return AWSStack

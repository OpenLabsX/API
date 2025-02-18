import uuid
from src.app.validators.id import is_valid_uuid4

def test_valid_uuid4() -> None:
    """Test valid uuid4 validation."""
    for _ in range(5):
        test_uuid = uuid.uuid4()
        assert is_valid_uuid4(test_uuid)
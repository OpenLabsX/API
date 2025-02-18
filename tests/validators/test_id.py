import uuid

from src.app.validators.id import is_valid_uuid4


def test_valid_uuid4() -> None:
    """Test we get true for valid uuid4 strings."""
    for _ in range(5):
        test_uuid = uuid.uuid4()
        assert is_valid_uuid4(str(test_uuid))


def test_invalid_uuid4() -> None:
    """Test we get false for invalid uuid4 strings."""
    for _ in range(5):
        invalid_uuid = str(uuid.uuid4())[:-1]
        assert not is_valid_uuid4(invalid_uuid)

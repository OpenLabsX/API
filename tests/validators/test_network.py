from src.app.validators.network import is_valid_hostname, is_valid_disk_size
from src.app.enums.operating_systems import OpenLabsOS

def test_valid_hostnames() -> None:
    """Test valid hostnames."""
    valid_hostnames: list[str] = [
        "example.com",
        "sub.example.com",
        "localhost",
        "my-site123.org",
        "a.co",
        "example.co.uk",
        "example.com.",  # With trailing dot
        "xn--d1acpjx3f.xn--p1ai",  # Punycode for international domains
        "example",
        "example-host-1",
    ]

    for hostname in valid_hostnames:
        assert is_valid_hostname(hostname) is True


def test_invalid_hostnames() -> None:
    """Test invalid hostnames."""
    invalid_hostnames: list[str] = [
        "",  # Empty string
        "-example.com",  # Starts with a hyphen
        "example-.com",  # Ends with a hyphen
        "exa_mple.com",  # Underscore is invalid
        "example..com",  # Double dot
        "123.456.789.0",  # All numeric TLD
        "example.123",  # Numeric TLD
        "a" * 64 + ".com",  # Label too long (>63)
        "a" * 254 + ".com",  # Hostname too long (>253)
        "example!.com",  # Special character '!' invalid
    ]

    for hostname in invalid_hostnames:
        assert is_valid_hostname(hostname) is False


def test_hostname_with_trailing_dot() -> None:
    """Test hostname with a trailing dot."""
    assert is_valid_hostname("example.com.") is True
    assert is_valid_hostname("example..com.") is False


def test_hostname_length_limits() -> None:
    """Test hostname length limits."""
    valid_hostname = ".".join(
        ["a" * 63] * 4
    )  # Total length = 63*4 + 3 dots = 255 (valid without trailing dot)
    invalid_hostname = valid_hostname + "a"

    assert (
        is_valid_hostname(valid_hostname[:-2]) is True
    )  # Adjust to fit within 253 limit
    assert is_valid_hostname(invalid_hostname) is False


def test_numeric_tld() -> None:
    """Test hostnames with numeric TLDs."""
    assert is_valid_hostname("example.123") is False
    assert is_valid_hostname("123.example") is True

def test_valid_host_size() -> None:
    """Test host disk size minimums."""
    assert is_valid_disk_size(OpenLabsOS.DEBIAN_11, 10)
    assert is_valid_disk_size(OpenLabsOS.WINDOWS_2016, 32)
    assert not is_valid_disk_size(OpenLabsOS.WINDOWS_2016, 10)

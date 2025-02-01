import re


def is_valid_hostname(hostname: str) -> bool:
    """Check if string is a valid hostname based on RRFC 1035.

    Args:
    ----
        hostname (str): String to check.

    Returns:
    -------
        bool: True if valid hostname. False otherwise.

    """
    max_hostname_length = 253

    if not hostname:
        return False

    if hostname[-1] == ".":
        # strip exactly one dot from the right, if present
        hostname = hostname[:-1]
    if len(hostname) > max_hostname_length:
        return False

    labels = hostname.split(".")

    # the TLD must be not all-numeric
    if re.match(r"[0-9]+$", labels[-1]):
        return False

    allowed = re.compile(r"(?!-)[a-z0-9-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(label) for label in labels)

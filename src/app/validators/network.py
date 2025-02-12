import re
from ipaddress import IPv4Network


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


def max_num_hosts_in_subnet(subnet: IPv4Network) -> int:
    """Get the max number of usable hosts in a subnet.

    Args:
    ----
        subnet (IPv4Network): IPv4 subnet network.

    Returns:
    -------
        int: Max number of usable hosts.

    """
    total_addresses = subnet.num_addresses
    multi_host_subnet_prefix_max = 31

    # If we can fit more than one host on the subnet
    # then subtract router and broadcast addresses
    if subnet.prefixlen < multi_host_subnet_prefix_max:
        return total_addresses - 2

    return total_addresses

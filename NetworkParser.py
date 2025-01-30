from enums.providers import OpenLabsProvider
from enums.specs import OpenLabsSpec
from ipaddress import IPv4Network

class OpenLabsHost:
    """Host object for OpenLabs"""
    def __init__(self, name: str, spec: OpenLabsSpec, size: int, tags: list[str]) -> None:
        """
        Initialize an OpenLabsHost object

        Parameters:
            name: Hostname machine will be initialized with
            spec: Ram and CPU for machine. Can be OpenLabsSpec{TINY, SMALL, MEDIUM, LARGE, HUGE}
            size: Size in GB of disk for machine
            tags: Optional list of tags that identify machine. Can be used for plugins
        """
        self.__name: str = name
        self.__spec: OpenLabsSpec = spec
        self.__size: int = size
        self.__tags: list[str] = tags

class OpenLabsSubnet:
    """Subnet object for OpenLabs"""
    def __init__(self, cidr: str, name: str, hosts: list[OpenLabsHost]) -> None:
        """
        Initialize an OpenLabsVPC object

        Parameters:
            cidr: VPC with cidr range
            name: Name Subnet will be initialized with
            hosts: List of OpenLabsHost. All hosts that will be created in subnet
        """
        self.__cidr: IPv4Network = IPv4Network(cidr)
        self.__name: str = name
        self.__hosts: list[OpenLabsHost] = hosts

class OpenLabsVPC:
    """VPC object for OpenLabs"""
    def __init__(self, cidr: str, name: str, subnets: list[OpenLabsSubnet]) -> None:
        """
        Initialize an OpenLabsVPC object

        Parameters:
            cidr: Subnet with cidr range
            name: Name VPC will be initialized with
            subnets: List of OpenLabsSubnet. All subnets that will be created in VPC
        """
        self.__cidr: IPv4Network = IPv4Network(cidr)
        self.__name: str = name
        self.__subnets: list[OpenLabsSubnet] = subnets


class OpenLabsRange:
    """Range object for OpenLabs"""
    def __init__(self, vpc: OpenLabsVPC, provider: OpenLabsProvider, vnc: bool = False, vpn: bool = False) -> None:
        """
        Initialize an OpenLabsRange object

        Parameters:
            vpc: OpenLabsVPC object. None will use default VPC for provider
            provider: Provider to be used for network. Can be OpenLabsProvider{AWS, AZURE}
            vnc: Should OpenLabs set up VNC for you
            vpn: Should OpenLabs set up VPN for you
        """
        self.__vpc: OpenLabsVPC = vpc
        self.__provider: OpenLabsProvider = provider
        self.__vnc: bool = vnc
        self.__vpn: bool = vpn
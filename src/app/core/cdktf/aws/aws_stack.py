from cdktf import TerraformStack
from cdktf_cdktf_provider_aws.eip import Eip
from cdktf_cdktf_provider_aws.instance import Instance
from cdktf_cdktf_provider_aws.internet_gateway import InternetGateway
from cdktf_cdktf_provider_aws.key_pair import KeyPair
from cdktf_cdktf_provider_aws.nat_gateway import NatGateway
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.route import Route
from cdktf_cdktf_provider_aws.route_table import RouteTable
from cdktf_cdktf_provider_aws.route_table_association import RouteTableAssociation
from cdktf_cdktf_provider_aws.security_group import SecurityGroup
from cdktf_cdktf_provider_aws.security_group_rule import SecurityGroupRule
from cdktf_cdktf_provider_aws.subnet import Subnet
from cdktf_cdktf_provider_aws.vpc import Vpc
from constructs import Construct

from ....enums.specs import AWS_SPEC_MAP
from ....schemas.openlabs import OpenLabsRange


class AWSStack(TerraformStack):
    """Stack for generating terraform for AWS."""

    def __init__(
        self, scope: Construct, cdktfid: str, cyber_range: OpenLabsRange
    ) -> None:
        """Initialize AWS terraform stack.

        Args:
        ----
            self (AWSStack): AWSStack class.
            scope (Construct): CDKTF app
            cdktfid (str): Unique ID for CDKTF app

        Returns:
        -------
            None

        """
        super().__init__(scope, cdktfid)

        # AWS Provider
        AwsProvider(self, "AWS", region="us-east-1")

        # Step 1: Create a VPC
        vpc = Vpc(
            self,
            cyber_range.vpc.name,
            cidr_block=str(cyber_range.vpc.cidr),
            enable_dns_support=True,
            enable_dns_hostnames=True,
            tags={"Name": cyber_range.vpc.name},
        )

        # Function to derive a subnet CIDR from the VPC CIDR
        def modify_cidr(vpc_cidr: str, new_third_octet: int) -> str:
            ip_part, prefix = vpc_cidr.split("/")
            octets = ip_part.split(".")
            octets[2] = str(new_third_octet)  # Change the third octet
            octets[3] = "0"  # Explicitly set the fourth octet to 0
            return f"{'.'.join(octets)}/24"  # Convert back to CIDR

        # Generate the new subnet CIDR with third octet = 99
        public_subnet_cidr = modify_cidr(str(cyber_range.vpc.cidr), 99)

        # Step 2: Create a Public Subnet for the Jump Box
        public_subnet = Subnet(
            self,
            "RangePublicSubnet",
            vpc_id=vpc.id,
            cidr_block=public_subnet_cidr,
            map_public_ip_on_launch=True,  # Enable public IP auto-assignment
            availability_zone="us-east-1a",
            tags={"Name": "RangePublicSubnet"},
        )

        # Step 3: Create an Internet Gateway for Public Subnet
        igw = InternetGateway(
            self,
            "RangeInternetGateway",
            vpc_id=vpc.id,
            tags={"Name": "RangeInternetGateway"},
        )

        # Step 4: Create a NAT Gateway for Private Subnet with EIP
        eip = Eip(
            self, "RangeNatEIP", tags={"Name": "RangeNatEIP"}
        )  # Elastic IP for NAT Gateway
        nat_gateway = NatGateway(
            self,
            "RangeNatGateway",
            subnet_id=public_subnet.id,  # NAT must be in a public subnet
            allocation_id=eip.id,
            tags={"Name": "RangeNatGateway"},
        )

        # Step 5: Create the key access to all instances provisioned on AWS
        key_pair = KeyPair(
            self,
            "JumpBoxKeyPair",
            key_name="cdktf-key",
            public_key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8URIMqVKb6EAK4O+E+9g8df1uvcOfpvPFl7sQrX7KM email@example.com",  # NOTE: Hardcoded key, will need a way to dynamically add a key to user instances
            tags={"Name": "cdktf-public-key"},
        )

        # Step 6: Create a Route Table for Public Subnet with association
        public_route_table = RouteTable(
            self,
            "RangePublicRouteTable",
            vpc_id=vpc.id,
            tags={"Name": "RangePublicRouteTable"},
        )
        Route(
            self,
            "RangePublicInternetRoute",
            route_table_id=public_route_table.id,
            destination_cidr_block="0.0.0.0/0",  # Allow internet access
            gateway_id=igw.id,
        )
        RouteTableAssociation(
            self,
            "RangePublicRouteAssociation",
            subnet_id=public_subnet.id,
            route_table_id=public_route_table.id,
        )

        # Step 7: Create a Route Table for Private Subnet (Using NAT)
        private_route_table = RouteTable(
            self,
            "RangePrivateRouteTable",
            vpc_id=vpc.id,
            tags={"Name": "RangePrivateRouteTable"},
        )
        Route(
            self,
            "RangePrivateNatRoute",
            route_table_id=private_route_table.id,
            destination_cidr_block="0.0.0.0/0",  # Allow internet access
            nat_gateway_id=nat_gateway.id,  # Route through NAT Gateway
        )

        # Step 8: Create Security Group and Rules for Jump Box (only allow SSH directly into jump box, for now)
        jumpbox_sg = SecurityGroup(
            self,
            "RangeJumpBoxSecurityGroup",
            vpc_id=vpc.id,
            tags={"Name": "RangeJumpBoxSecurityGroup"},
        )
        SecurityGroupRule(
            self,
            "RangeAllowJumpBoxSSHFromInternet",
            type="ingress",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],  # Allow SSH from anywhere
            security_group_id=jumpbox_sg.id,
        )
        SecurityGroupRule(
            self,
            "RangeJumpBoxAllowOutbound",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            security_group_id=jumpbox_sg.id,
        )

        # Step 9. Dynamically Create Internal Private Subnets from provided list (NOTE: Will eventually create from passed in CyberRange object). First grab all passed in subnet CIDRs to use for making the relevan security group rules
        private_cidrs = [str(subnet.cidr) for subnet in cyber_range.vpc.subnets]

        # Step 10: Create Security Group for Private EC2 Instances
        private_sg = SecurityGroup(
            self,
            "RangePrivateInternalSecurityGroup",
            vpc_id=vpc.id,
            tags={"Name": "RangePrivateInternalSecurityGroup"},
        )
        SecurityGroupRule(
            self,
            "RangeAllowAllTrafficFromJumpBox",
            type="ingress",
            from_port=0,
            to_port=0,
            protocol="-1",
            security_group_id=private_sg.id,
            source_security_group_id=jumpbox_sg.id,  # Allow all traffic from Jump Box
        )
        SecurityGroupRule(
            self,
            "RangeAllowInternalTraffic",  # Allow all internal subnets to communicate ONLY with each other
            type="ingress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=private_cidrs,  # Use dynamically created CIDR blocks
            security_group_id=private_sg.id,
        )
        SecurityGroupRule(
            self,
            "RangeAllowPrivateOutbound",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            security_group_id=private_sg.id,
        )

        # Step 11: Create Jump Box
        Instance(
            self,
            "JumpBoxInstance",
            ami="ami-014f7ab33242ea43c",  # Amazon Ubuntu 20.04 AMI
            instance_type="t2.micro",
            subnet_id=public_subnet.id,
            vpc_security_group_ids=[jumpbox_sg.id],
            associate_public_ip_address=True,  # Ensures public IP is assigned
            key_name=key_pair.key_name,  # Use the generated key pair
            tags={"Name": "JumpBox"},
        )

        # Step 12: Create private subnets with their respecitve EC2 instances
        for subnet in cyber_range.vpc.subnets:
            new_subnet = Subnet(
                self,
                subnet.name,
                vpc_id=vpc.id,
                cidr_block=str(subnet.cidr),
                availability_zone="us-east-1a",
                tags={"Name": subnet.name},
            )
            RouteTableAssociation(
                self,
                subnet.name + "RouteAssociation",
                subnet_id=new_subnet.id,
                route_table_id=private_route_table.id,
            )
            for host in subnet.hosts:  # Create specified instances in the given subnet
                Instance(
                    self,
                    host.hostname,
                    ami="ami-014f7ab33242ea43c",  # WIll need to grab from update OpenLabsRange object
                    instance_type=AWS_SPEC_MAP[host.spec],
                    subnet_id=new_subnet.id,
                    vpc_security_group_ids=[private_sg.id],
                    key_name=key_pair.key_name,  # Use the generated key pair
                    tags={"Name": host.hostname},
                )

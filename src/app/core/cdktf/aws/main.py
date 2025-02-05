#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from cdktf_cdktf_provider_aws.vpc import Vpc 
from cdktf_cdktf_provider_aws.provider import AwsProvider
from cdktf_cdktf_provider_aws.subnet import Subnet
from cdktf_cdktf_provider_aws.internet_gateway import InternetGateway
from cdktf_cdktf_provider_aws.route_table import RouteTable
from cdktf_cdktf_provider_aws.route import Route
from cdktf_cdktf_provider_aws.route_table_association import RouteTableAssociation
from cdktf_cdktf_provider_aws.instance import Instance
from cdktf_cdktf_provider_aws.security_group import SecurityGroup
from cdktf_cdktf_provider_aws.security_group_rule import SecurityGroupRule
from cdktf_cdktf_provider_aws.nat_gateway import NatGateway
from cdktf_cdktf_provider_aws.eip import Eip
from cdktf_cdktf_provider_aws.key_pair import KeyPair


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # AWS Provider
        AwsProvider(self, "AWS", region="us-east-1")

        ### TEST: Define internal subnet configurations statically to test deployment of multiple subnets
        internal_subnets = [
            {"name": "PrivateSubnet1", "cidr": "10.21.2.0/24", "az": "us-east-1a", "instances": [{"name": "PrivateInstance1"}, {"name": "PrivateInstance2"}, {"name": "PrivateInstance3"},]},
            {"name": "PrivateSubnet2", "cidr": "10.21.3.0/24", "az": "us-east-1a", "instances": [{"name": "PrivateInstance1"}, {"name": "PrivateInstance2"}, {"name": "PrivateInstance3"},]},
            {"name": "PrivateSubnet3", "cidr": "10.21.4.0/24", "az": "us-east-1a", "instances": [{"name": "PrivateInstance1"}, {"name": "PrivateInstance2"}, {"name": "PrivateInstance3"},]},
        ]

        # Step 1: Create a VPC
        vpc = Vpc(self, "TestVPC",
                  cidr_block="10.21.0.0/16",
                  enable_dns_support=True,
                  enable_dns_hostnames=True,
                  tags={
                      "Name": "TestVPC"
                  })

        # Step 2: Create a Public Subnet for the Jump Box
        public_subnet = Subnet(self, "TestPublicSubnet",
            vpc_id=vpc.id,
            cidr_block="10.21.1.0/24",
            map_public_ip_on_launch=True,  # Enable public IP auto-assignment
            availability_zone="us-east-1a",
            tags={"Name": "TestPublicSubnet"} 
        )

        # Step 3: Create an Internet Gateway for Public Subnet
        igw = InternetGateway(self, "TestInternetGateway",
            vpc_id=vpc.id,
            tags={"Name": "TestInternetGateway"}
        )

        # Step 4: Create a NAT Gateway for Private Subnet with EIP
        eip = Eip(self, "TestNatEIP", tags={"Name": "TestNatEIP"})  # Elastic IP for NAT Gateway
        nat_gateway = NatGateway(self, "TestNatGateway",
            subnet_id=public_subnet.id,  # NAT must be in a public subnet
            allocation_id=eip.id,
            tags={"Name": "TestNatGateway"}
        )

        # Step 5: Create the key access to all instances provisioned on AWS
        key_pair = KeyPair(self, "JumpBoxKeyPair",
            key_name="cdktf-key",
            public_key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8URIMqVKb6EAK4O+E+9g8df1uvcOfpvPFl7sQrX7KM email@example.com", # NOTE: Hardcoded key, will need a way to dynamically add a key to user instances
            tags={"Name": "cdktf-public-key"}
        )

        # Step 6: Create a Route Table for Public Subnet with association
        public_route_table = RouteTable(self, "TestPublicRouteTable", vpc_id=vpc.id, tags={"Name": "TestPublicRouteTable"})
        Route(self, "TestPublicInternetRoute",
            route_table_id=public_route_table.id,
            destination_cidr_block="0.0.0.0/0",  # Allow internet access
            gateway_id=igw.id
        )
        RouteTableAssociation(self, "TestPublicRouteAssociation",
            subnet_id=public_subnet.id,
            route_table_id=public_route_table.id
        )

        # Step 7: Create a Route Table for Private Subnet (Using NAT)
        private_route_table = RouteTable(self, "TestPrivateRouteTable", vpc_id=vpc.id, tags={"Name": "TestPrivateRouteTable"})
        Route(self, "TestPrivateNatRoute",
            route_table_id=private_route_table.id,
            destination_cidr_block="0.0.0.0/0",  # Allow internet access
            nat_gateway_id=nat_gateway.id  # Route through NAT Gateway
        )

        # Step 8: Create Security Group and Rules for Jump Box (only allow SSH directly into jump box, for now)
        jumpbox_sg = SecurityGroup(self, "TestJumpBoxSecurityGroup",
            vpc_id=vpc.id,
            tags={"Name": "TestJumpBoxSecurityGroup"}
        )
        SecurityGroupRule(self, "TestAllowJumpBoxSSHFromInternet",
            type="ingress",
            from_port=22,
            to_port=22,
            protocol="tcp",
            cidr_blocks=["0.0.0.0/0"],  # Allow SSH from anywhere
            security_group_id=jumpbox_sg.id
        )
        SecurityGroupRule(self, "TestJumpBoxAllowOutbound",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            security_group_id=jumpbox_sg.id
        )

        # Step 9. Dynamically Create Internal Private Subnets from provided list (NOTE: Will eventually create from passed in CyberRange object). First grab all passed in subnet CIDRs to use for making the relevan security group rules
        private_cidrs = []
        for subnet in internal_subnets:
            private_cidrs.append(subnet["cidr"])

        # Step 10: Create Security Group for Private EC2 Instances
        private_sg = SecurityGroup(self, "TestPrivateInternalEC2SecurityGroup",
            vpc_id=vpc.id,
            tags={"Name": "TestPrivateInternalEc2SecurityGroup"}
        )
        SecurityGroupRule(self, "AllowAllTrafficFromJumpBox",
            type="ingress",
            from_port=0,
            to_port=0,
            protocol="-1",
            security_group_id=private_sg.id,
            source_security_group_id=jumpbox_sg.id  # Allow all traffic from Jump Box
        )
        
        SecurityGroupRule(self, "AllowInternalTraffic", # Allow all internal subnets to communicate ONLY with each other
            type="ingress",
            from_port=0,  
            to_port=0,    
            protocol="-1",    
            cidr_blocks=private_cidrs,  # Use dynamically created CIDR blocks
            security_group_id=private_sg.id
        )
        SecurityGroupRule(self, "AllowPrivateOutbound",
            type="egress",
            from_port=0,
            to_port=0,
            protocol="-1",
            cidr_blocks=["0.0.0.0/0"],
            security_group_id=private_sg.id
        )

        # Step 11: Create Jump Box
        jumpbox = Instance(self, "JumpBoxInstance",
            ami="ami-014f7ab33242ea43c",  # Amazon Ubuntu 20.04 AMI
            instance_type="t2.micro",
            subnet_id=public_subnet.id,
            vpc_security_group_ids=[jumpbox_sg.id],
            associate_public_ip_address=True,  # Ensures public IP is assigned
            key_name=key_pair.key_name, # Use the generated key pair
            tags={"Name": "JumpBox"}
        )

        # Step 12: Create private subnets with their respecitve EC2 instances
        for subnet in internal_subnets:
            new_subnet = Subnet(self, subnet["name"],
                vpc_id=vpc.id,
                cidr_block=subnet["cidr"],
                availability_zone=subnet["az"],
                tags={"Name": subnet["name"]}
            )
            private_cidrs.append(subnet["cidr"])
            RouteTableAssociation(self, subnet["name"] + "RouteAssociation",
                subnet_id=new_subnet.id,
                route_table_id=private_route_table.id
            )
            for instance in subnet["instances"]: # Create specified instances in the given subnet
                Instance(self, subnet["name"] + instance["name"],
                ami="ami-014f7ab33242ea43c",
                instance_type="t2.micro",
                subnet_id=new_subnet.id,
                vpc_security_group_ids=[private_sg.id],
                key_name=key_pair.key_name, # Use the generated key pair
                tags={"Name": subnet["name"] + instance["name"]}
            )

app = App()
MyStack(app, "aws")

app.synth()

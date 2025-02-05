#!/usr/bin/env python
from constructs import Construct
from cdktf import App, TerraformStack, TerraformOutput
from imports.aws.vpc import Vpc 
from imports.aws.provider import AwsProvider
from imports.aws.subnet import Subnet
from imports.aws.internet_gateway import InternetGateway
from imports.aws.route_table import RouteTable
from imports.aws.route import Route
from imports.aws.route_table_association import RouteTableAssociation
from imports.aws.instance import Instance
from imports.aws.security_group import SecurityGroup
from imports.aws.security_group_rule import SecurityGroupRule
from imports.aws.nat_gateway import NatGateway
from imports.aws.eip import Eip
from imports.aws.key_pair import KeyPair


class MyStack(TerraformStack):
    def __init__(self, scope: Construct, id: str):
        super().__init__(scope, id)

        # AWS Provider
        AwsProvider(self, "AWS", region="us-east-1")

        ### TEST: Define internal subnet configurations statically to test deployment of multiple subnets
        internal_subnets = [
            {"name": "PrivateSubnet1", "cidr": "10.21.2.0/24", "az": "us-east-1a"},
            {"name": "PrivateSubnet2", "cidr": "10.21.3.0/24", "az": "us-east-1a"},
            {"name": "PrivateSubnet3", "cidr": "10.21.4.0/24", "az": "us-east-1a"},
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

        # # Step 3: Create a Private Subnet for the EC2 instanes
        # private_subnet = Subnet(self, "PrivateSubnet",
        #     vpc_id=vpc.id,
        #     cidr_block="10.21.2.0/24",
        #     map_public_ip_on_launch=False,  # No public IP for instances
        #     availability_zone="us-east-1a",
        #     tags={"Name": "PrivateSubnet"} 
        # )

        # Step 4: Create an Internet Gateway for Public Subnet
        igw = InternetGateway(self, "TestInternetGateway",
            vpc_id=vpc.id,
            tags={"Name": "TestInternetGateway"}
        )

        # Step 5: Create a NAT Gateway for Private Subnet with EIP
        eip = Eip(self, "TestNatEIP", tags={"Name": "TestNatEIP"})  # Elastic IP for NAT Gateway
        nat_gateway = NatGateway(self, "TestNatGateway",
            subnet_id=public_subnet.id,  # NAT must be in a public subnet
            allocation_id=eip.id,
            tags={"Name": "TestNatGateway"}
        )

        # Step 6: Create a Route Table for Public Subnet 
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

        # Step 8. Dynamically Create Internal Private Subnets from provided list (NOTE: Will eventually create from passed in CyberRange object)
        private_subnets = []
        private_cidrs = []
        for subnet in internal_subnets:
            new_subnet = Subnet(self, subnet["name"],
                vpc_id=vpc.id,
                cidr_block=subnet["cidr"],
                availability_zone=subnet["az"],
                tags={"Name": subnet["name"]}
            )
            private_subnets.append(new_subnet)
            private_cidrs.append(subnet["cidr"])
            RouteTableAssociation(self, subnet["name"] + "RouteAssociation",
                subnet_id=new_subnet.id,
                route_table_id=private_route_table.id
            )

        # RouteTableAssociation(self, "PrivateRouteAssoc",
        #     subnet_id=private_subnet.id,
        #     route_table_id=private_route_table.id
        # )

        # Step 9: Associate Each Private Subnet with the Private Route Table
        # for private_subnet in private_subnets:
        #     route_association_name = str(private_subnet.id) + "RouteAssociation"
        #     RouteTableAssociation(self, route_association_name,
        #         subnet_id=private_subnet.id,
        #         route_table_id=private_route_table.id
        #     )

        # Step 10: Create Security Group for Jump Box
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

        # Step 11: Create Security Group for Private EC2 Instances
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
            source_security_group_id=jumpbox_sg.id  # Allow SSH only from Jump Box
        )
        # Allow all internal subnets to communicate ONLY with each other
        SecurityGroupRule(self, "AllowInternalTraffic",
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

        # Step 12: Create the Jump Box (Bastion Host) and key access to the jump box
        key_pair = KeyPair(self, "JumpBoxKeyPair",
            key_name="cdktf-key",
            public_key="ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIH8URIMqVKb6EAK4O+E+9g8df1uvcOfpvPFl7sQrX7KM email@example.com", # NOTE: Hardcoded key, will need a way to dynamically add a key to user instances
            tags={"Name": "cdktf-public-key"}
        )

        jumpbox = Instance(self, "JumpBoxInstance",
            ami="ami-014f7ab33242ea43c",  # Amazon Ubuntu 20.04 AMI
            instance_type="t2.micro",
            subnet_id=public_subnet.id,
            vpc_security_group_ids=[jumpbox_sg.id],
            associate_public_ip_address=True,  # Ensures public IP is assigned
            key_name=key_pair.key_name, # Use the generated key pair
            tags={"Name": "JumpBox"}
        )

        # # Step 13: Create Private EC2 Instance using same key access for intial deployment
        # private_ec2 = Instance(self, "PrivateEC2Instance",
        #     ami="ami-014f7ab33242ea43c",  # Amazon Ubuntu 20.04 AMI
        #     instance_type="t2.micro",
        #     subnet_id=private_subnet.id,
        #     vpc_security_group_ids=[private_sg.id],
        #     key_name=key_pair.key_name, # Use the generated key pair
        #     tags={"Name": "PrivateEC2"}
        # )

        # Step 14: Create Internal EC2 Instances in Private Subnets
        for i, private_subnet in enumerate(private_subnets):
            Instance(self, f"PrivateInstance{i+1}",
                ami="ami-014f7ab33242ea43c",
                instance_type="t2.micro",
                subnet_id=private_subnet.id,
                vpc_security_group_ids=[private_sg.id],
                key_name=key_pair.key_name, # Use the generated key pair
                tags={"Name": f"PrivateInstance{i+1}"}
            )

app = App()
MyStack(app, "aws")

app.synth()

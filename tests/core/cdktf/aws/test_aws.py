import json
import shutil
import uuid
from typing import Any

from src.app.schemas.openlabs_range_schema import OpenLabsRangeSchema
from src.app.utils.cdktf_utils import create_cdktf_dir
from tests.conftest import skip_if_env

# Valid payload for comparison
valid_one_all_range_payload: dict[str, Any] = {
    "vpcs": [
        {
            "cidr": "192.168.0.0/16",
            "name": "example-vpc-1",
            "subnets": [
                {
                    "cidr": "192.168.1.0/24",
                    "name": "example-subnet-1",
                    "hosts": [
                        {
                            "hostname": "example-host-1",
                            "os": "debian_11",
                            "spec": "tiny",
                            "size": 8,
                            "tags": ["web", "linux"],
                        }
                    ],
                }
            ],
        }
    ],
    "provider": "aws",
    "name": "example-range-1",
    "vnc": False,
    "vpn": False,
}


@skip_if_env(var="SKIP_CDKTF_TESTS", reason="Skipping CDKTF tests")
def test_create_aws_stack_synth_one_all() -> None:
    """Test that the terraform JSON output matches the input range template.

    This is with a range that has only one VPC, Subnet, and Host.
    """
    # Prevent slow pytest imports
    from src.app.core.cdktf.aws.aws import create_aws_stack

    cyber_range = OpenLabsRangeSchema.model_validate(
        valid_one_all_range_payload, from_attributes=True
    )
    cyber_range_id = uuid.uuid4()
    test_dir = create_cdktf_dir()

    stack_name = create_aws_stack(cyber_range, test_dir, cyber_range_id)
    synth_output_dir = f"{test_dir}/stacks/{stack_name}"

    cdktf_json_content = ""
    with open(f"{synth_output_dir}/cdk.tf.json", "r", encoding="utf-8") as file:
        cdktf_json_content = file.read()
    cdktf_json: dict[str, Any] = json.loads(cdktf_json_content)

    # Check that there is content first
    assert cdktf_json

    # ====== Validate Terraform Output ====== #
    cdktf_resources: dict[str, Any] = cdktf_json["resource"]

    # Provider
    cdktf_provider = cdktf_json["provider"]
    assert len(cdktf_provider) == 1  # Only AWS provider
    assert cyber_range.provider.value in cdktf_provider

    # VPC
    cdktf_vpcs = cdktf_resources["aws_vpc"]
    assert len(cdktf_vpcs) == 1
    assert cyber_range.vpcs[0].name in cdktf_vpcs
    assert (  # CIDR Block
        str(cyber_range.vpcs[0].cidr)
        == cdktf_resources["aws_vpc"][cyber_range.vpcs[0].name]["cidr_block"]
    )

    # Subnet
    cdktf_subnets = cdktf_resources["aws_subnet"]
    cyber_range_subnets = cyber_range.vpcs[0].subnets
    assert (
        len(cdktf_subnets) == len(cyber_range_subnets) + 1
    )  # Extra for RangePublicSubnet
    assert cyber_range_subnets[0].name in cdktf_subnets
    assert (
        str(cyber_range_subnets[0].cidr)
        == cdktf_resources["aws_subnet"][cyber_range_subnets[0].name]["cidr_block"]
    )

    # Hosts
    cdktf_hosts = cdktf_resources["aws_instance"]
    cyber_range_hosts = cyber_range.vpcs[0].subnets[0].hosts

    # Jumpbox
    assert len(cdktf_hosts) >= 1  # Must be at least one host if JumpBox is default
    assert "JumpBoxInstance" in cdktf_hosts

    # Template Hosts
    assert len(cdktf_hosts) == len(cyber_range_hosts) + 1  # Extra for Jumpbox
    assert cyber_range_hosts[0].hostname in cdktf_hosts

    # ====== Clean Up ====== #
    shutil.rmtree(test_dir)

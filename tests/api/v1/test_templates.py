import copy
import json
import uuid
from typing import Any

from fastapi import status
from httpx import AsyncClient

from src.app.schemas.openlabs_host_schema import OpenLabsHostSchema
from src.app.schemas.openlabs_subnet_schema import OpenLabsSubnetHeaderSchema

from .config import BASE_ROUTE

###### Test /template/range #######

# Valid payload for comparison
valid_range_payload: dict[str, Any] = {
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

valid_vpc_payload: dict[str, Any] = {
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

valid_subnet_payload: dict[str, Any] = {
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

valid_host_payload: dict[str, Any] = {
    "hostname": "example-host-1",
    "os": "debian_11",
    "spec": "tiny",
    "size": 8,
    "tags": ["web", "linux"],
}


async def test_template_range_get_all_empty_list(client: AsyncClient) -> None:
    """Test that we get a 404 response when there are no range templates."""
    response = await client.get(f"{BASE_ROUTE}/templates/ranges")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_vpc_get_all_empty_list(client: AsyncClient) -> None:
    """Test that we get a 404 response when there are no vpc templates."""
    response = await client.get(f"{BASE_ROUTE}/templates/vpcs")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_subnet_get_all_empty_list(client: AsyncClient) -> None:
    """Test that we get a 404 response when there are no subnet templates."""
    response = await client.get(f"{BASE_ROUTE}/templates/subnets")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_host_get_all_empty_list(client: AsyncClient) -> None:
    """Test that we get a 404 response when there are no template templates."""
    response = await client.get(f"{BASE_ROUTE}/templates/hosts")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_range_get_non_empty_list(client: AsyncClient) -> None:
    """Test all templates to see that we get a 200 response and that correct UUIDs exist."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/ranges", json=valid_range_payload
    )
    range_template_id = response.json()["id"]
    assert response.status_code == status.HTTP_200_OK

    response = await client.get(f"{BASE_ROUTE}/templates/ranges")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1

    non_nested_range_dict = copy.deepcopy(valid_range_payload)
    del non_nested_range_dict["vpcs"]
    assert response_json[0] == {"id": range_template_id, **non_nested_range_dict}


async def test_template_all_get_non_standalone_templates(client: AsyncClient) -> None:
    """Test that, after uploading range template previously, we have all non-standalone templates."""
    response = await client.get(f"{BASE_ROUTE}/templates/vpcs?standalone_only=false")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1

    non_nested_vpc_dict = copy.deepcopy(valid_vpc_payload)
    del non_nested_vpc_dict["subnets"]
    assert response_json[0] == {"id": response_json[0]["id"], **non_nested_vpc_dict}

    response = await client.get(f"{BASE_ROUTE}/templates/subnets?standalone_only=false")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1

    non_nested_subnet_dict = copy.deepcopy(valid_subnet_payload)
    del non_nested_subnet_dict["hosts"]
    assert response_json[0] == {"id": response_json[0]["id"], **non_nested_subnet_dict}

    response = await client.get(f"{BASE_ROUTE}/templates/hosts?standalone_only=false")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1

    non_nested_host_dict = copy.deepcopy(valid_host_payload)
    assert response_json[0] == {"id": response_json[0]["id"], **non_nested_host_dict}


async def test_template_vpc_get_non_empty_list(client: AsyncClient) -> None:
    """Test all templates to see that we get a 200 response and that correct headers exist."""
    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=valid_vpc_payload)
    vpc_template_id = response.json()["id"]
    assert response.status_code == status.HTTP_200_OK

    response = await client.get(f"{BASE_ROUTE}/templates/vpcs?standalone_only=true")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) == 1

    non_nested_vpc_dict = copy.deepcopy(valid_vpc_payload)
    del non_nested_vpc_dict["subnets"]
    assert response_json[0] == {"id": vpc_template_id, **non_nested_vpc_dict}


async def test_template_subnet_get_non_empty_list(client: AsyncClient) -> None:
    """Test all templates to see that we get a 200 response and that correct headers exist."""
    # Create unique subnet object for this test
    unique_valid_subnet_payload = copy.deepcopy(valid_subnet_payload)
    unique_valid_subnet_payload["name"] = str(uuid.uuid4())

    response = await client.post(
        f"{BASE_ROUTE}/templates/subnets", json=unique_valid_subnet_payload
    )
    subnet_template_id = response.json()["id"]
    assert response.status_code == status.HTTP_200_OK

    response = await client.get(f"{BASE_ROUTE}/templates/subnets?standalone_only=true")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) >= 1  # Our subnet template must be in there

    # Dynamically build header object to avoid future updates breaking tests
    concat_dict = {"id": subnet_template_id, **unique_valid_subnet_payload}
    subnet_header_obj = OpenLabsSubnetHeaderSchema(**concat_dict)

    expected = json.loads(subnet_header_obj.model_dump_json())
    assert expected in response_json


async def test_template_host_get_non_empty_list(client: AsyncClient) -> None:
    """Test all templates to see that we get a 200 response and that correct headers exist."""
    # Create unique host object for this test
    unique_valid_host_payload = copy.deepcopy(valid_host_payload)
    unique_valid_host_payload["name"] = str(uuid.uuid4())

    response = await client.post(
        f"{BASE_ROUTE}/templates/hosts", json=unique_valid_host_payload
    )
    host_template_id = response.json()["id"]
    assert response.status_code == status.HTTP_200_OK

    response = await client.get(f"{BASE_ROUTE}/templates/hosts?standalone_only=true")
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert len(response_json) >= 1  # Our subnet template must be in there

    # Dynamically build header object to avoid future updates breaking tests
    concat_dict = {"id": host_template_id, **unique_valid_host_payload}
    host_header_obj = OpenLabsHostSchema(**concat_dict)

    expected = json.loads(host_header_obj.model_dump_json())
    assert expected in response_json


async def test_template_range_valid_payload(client: AsyncClient) -> None:
    """Test that we get a 200 and a valid uuid.UUID4 in response."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/ranges", json=valid_range_payload
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


async def test_template_range_invalid_vpc_cidr(client: AsyncClient) -> None:
    """Test for 422 response when VPC CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0][
        "cidr"
    ] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_invalid_subnet_cidr(client: AsyncClient) -> None:
    """Test for 422 response when subnet CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0][
        "cidr"
    ] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_invalid_vpc_subnet_cidr_contain(
    client: AsyncClient,
) -> None:
    """Test for 422 response when subnet CIDR is not contained in the VPC CIDR."""
    invalid_payload = copy.deepcopy(valid_range_payload)

    # VPC CIDR
    invalid_payload["vpcs"][0]["cidr"] = "192.168.0.0/16"

    # Subnet CIDR
    invalid_payload["vpcs"][0]["subnets"][0][
        "cidr"
    ] = "172.16.1.0/24"  # Assign the invalid CIDR block

    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_empty_tag(client: AsyncClient) -> None:
    """Test for a 422 response when a tag is empty."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0]["tags"].append("")
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_invalid_provider(client: AsyncClient) -> None:
    """Test for a 422 response when the provider is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["provider"] = "invalid_provider"  # Not a valid enum value
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_invalid_hostname(client: AsyncClient) -> None:
    """Test for a 422 response when a hostname is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0]["hostname"] = "-i-am-invalid"
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_duplicate_vpc_names(client: AsyncClient) -> None:
    """Test for a 422 response when multiple VPCs share the same name."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"].append(
        copy.deepcopy(invalid_payload["vpcs"][0])
    )  # Duplicate the first VPC
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_duplicate_subnet_names(client: AsyncClient) -> None:
    """Test for a 422 response when multiple subnets share the same name."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"].append(
        copy.deepcopy(invalid_payload["vpcs"][0]["subnets"][0])
    )
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_duplicate_host_hostnames(client: AsyncClient) -> None:
    """Test for a 422 response when multiple hosts share the same hostname."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"].append(
        copy.deepcopy(invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0])
    )
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_get_range(client: AsyncClient) -> None:
    """Test that we can retrieve the correct range after saving it in the database."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/ranges", json=valid_range_payload
    )
    assert response.status_code == status.HTTP_200_OK

    range_id = response.json()["id"]

    response = await client.get(f"{BASE_ROUTE}/templates/ranges/{range_id}")
    assert response.status_code == status.HTTP_200_OK

    # Add id to JSON to mimic GET response
    expected_response = {"id": range_id, **valid_range_payload}
    assert response.json() == expected_response


async def test_template_range_get_nonexistent_range(client: AsyncClient) -> None:
    """Test that we get a 404 error when requesting an nonexistent range in the database."""
    nonexistent_range_id = uuid.uuid4()
    response = await client.get(f"{BASE_ROUTE}/templates/ranges/{nonexistent_range_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_range_subnet_too_many_hosts(client: AsyncClient) -> None:
    """Test that we get a 422 error when more hosts in subnet that CIDR allows."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0][
        "cidr"
    ] = "192.168.1.0/31"  # Maximum 2 hosts

    # Add extra hosts
    for i in range(3):
        copy_host = copy.deepcopy(invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0])
        copy_host["hostname"] = copy_host["hostname"] + str(i)
        invalid_payload["vpcs"][0]["subnets"][0]["hosts"].append(copy_host)

    max_hosts_allowed = 2
    assert len(invalid_payload["vpcs"][0]["subnets"][0]["hosts"]) > max_hosts_allowed

    # Request
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_range_host_size_too_small(client: AsyncClient) -> None:
    """Test that we get a 422 error when the disk size of a host is too small."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0]["size"] = 2

    # Request
    response = await client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_vpc_valid_payload(client: AsyncClient) -> None:
    """Test that we get a 200 response and a valid uuid.UUID4 in response."""
    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=valid_vpc_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


async def test_template_vpc_invalid_cidr(client: AsyncClient) -> None:
    """Test that we get a 422 response when the VPC CIDR is invalid."""
    invalid_payload = copy.deepcopy(valid_vpc_payload)
    invalid_payload["cidr"] = "192.168.300.0/24"
    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_vpc_invalid_subnet_cidr(client: AsyncClient) -> None:
    """Test that we get a 422 response when the VPC subnet CIDR is invalid."""
    invalid_payload = copy.deepcopy(valid_vpc_payload)
    invalid_payload["subnets"][0]["cidr"] = "192.168.300.0/24"
    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_vpc_invalid_vpc_subnet_cidr_contain(
    client: AsyncClient,
) -> None:
    """Test that we get a 422 response when the subnet CIDR is not contained in the VPC CIDR."""
    invalid_payload = copy.deepcopy(valid_vpc_payload)

    # VPC CIDR
    invalid_payload["cidr"] = "192.168.0.0/16"

    # Subnet CIDR
    invalid_payload["subnets"][0]["cidr"] = "172.16.1.0/24"

    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_vpc_get_vpc(client: AsyncClient) -> None:
    """Test that we can retrieve the correct VPC after saving it in the database."""
    response = await client.post(f"{BASE_ROUTE}/templates/vpcs", json=valid_vpc_payload)
    assert response.status_code == status.HTTP_200_OK

    vpc_id = response.json()["id"]

    response = await client.get(f"{BASE_ROUTE}/templates/vpcs/{vpc_id}")
    assert response.status_code == status.HTTP_200_OK

    # Add id to JSON to mimic GET response
    expected_response = {"id": vpc_id, **valid_vpc_payload}
    assert response.json() == expected_response


async def test_template_vpc_get_nonexistent_vpc(client: AsyncClient) -> None:
    """Test that we get a 404 error when requesting a nonexistent vpc in the database."""
    nonexistent_vpc_id = uuid.uuid4()
    response = await client.get(f"{BASE_ROUTE}/templates/vpcs/{nonexistent_vpc_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_subnet_valid_payload(client: AsyncClient) -> None:
    """Test that we get a 200 reponse and a valid uuid.UUID4 in response."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/subnets", json=valid_subnet_payload
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


async def test_template_subnet_invalid_subnet_cidr(client: AsyncClient) -> None:
    """Test that we get a 422 response when the subnet CIDR is invalid."""
    invalid_payload = copy.deepcopy(valid_subnet_payload)
    invalid_payload["cidr"] = "192.168.300.0/24"
    response = await client.post(
        f"{BASE_ROUTE}/templates/subnets", json=invalid_payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_subnet_too_many_hosts(client: AsyncClient) -> None:
    """Test that we get a 422 response when more hosts in subnet than CIDR allows."""
    invalid_payload = copy.deepcopy(valid_subnet_payload)
    invalid_payload["cidr"] = "192.168.1.0/31"  # Maximum 2 hosts

    # Add extra hosts
    for i in range(3):
        copy_host = copy.deepcopy(invalid_payload["hosts"][0])
        copy_host["hostname"] = copy_host["hostname"] + str(i)
        invalid_payload["hosts"].append(copy_host)

    max_hosts_allowed = 2
    assert len(invalid_payload["hosts"]) > max_hosts_allowed

    # Request
    response = await client.post(
        f"{BASE_ROUTE}/templates/subnets", json=invalid_payload
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_template_subnet_get_subnet(client: AsyncClient) -> None:
    """Test that we can retrieve the correct subnet after saving it in the database."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/subnets", json=valid_subnet_payload
    )
    assert response.status_code == status.HTTP_200_OK

    subnet_id = response.json()["id"]

    response = await client.get(f"{BASE_ROUTE}/templates/subnets/{subnet_id}")
    assert response.status_code == status.HTTP_200_OK

    # Add id to JSON to mimic GET response
    expected_response = {"id": subnet_id, **valid_subnet_payload}
    assert response.json() == expected_response


async def test_template_subnet_get_nonexistent_subnet(client: AsyncClient) -> None:
    """Test that we get a 404 error when requesting a nonexistent subnet in the database."""
    nonexistent_subnet_id = uuid.uuid4()
    response = await client.get(
        f"{BASE_ROUTE}/templates/subnets/{nonexistent_subnet_id}"
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


async def test_template_host_valid_payload(client: AsyncClient) -> None:
    """Test that we get a 200 reponse and a valid uuid.UUID4 in response."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/hosts", json=valid_host_payload
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


async def test_template_host_get_host(client: AsyncClient) -> None:
    """Test that we can retrieve the correct host after saving it in the database."""
    response = await client.post(
        f"{BASE_ROUTE}/templates/hosts", json=valid_host_payload
    )
    assert response.status_code == status.HTTP_200_OK

    host_id = response.json()["id"]

    response = await client.get(f"{BASE_ROUTE}/templates/hosts/{host_id}")
    assert response.status_code == status.HTTP_200_OK

    # Add id to JSON to mimic GET response
    expected_response = {"id": host_id, **valid_host_payload}
    assert response.json() == expected_response


async def test_template_host_get_nonexistent_host(client: AsyncClient) -> None:
    """Test that we get a 404 error when requesting a nonexistent host in the database."""
    nonexistent_host_id = uuid.uuid4()
    response = await client.get(f"{BASE_ROUTE}/templates/hosts/{nonexistent_host_id}")
    assert response.status_code == status.HTTP_404_NOT_FOUND

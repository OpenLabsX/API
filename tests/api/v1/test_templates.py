import copy
import uuid
from typing import Any

from fastapi import status
from fastapi.testclient import TestClient

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
                            "size": 1,
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


def test_template_range_valid_payload(client: TestClient) -> None:
    """Test that we get a 200 and a valid uuid.UUID4 in response."""
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=valid_range_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


def test_template_range_invalid_vpc_cidr(client: TestClient) -> None:
    """Test for 422 response when VPC CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0][
        "cidr"
    ] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_subnet_cidr(client: TestClient) -> None:
    """Test for 422 response when subnet CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0][
        "cidr"
    ] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_vpc_subnet_cidr_contain(client: TestClient) -> None:
    """Test for 422 response when subnet CIDR is not contained in the VPC CIDR."""
    invalid_payload = copy.deepcopy(valid_range_payload)

    # VPC CIDR
    invalid_payload["vpcs"][0]["cidr"] = "192.168.0.0/16"

    # Subnet CIDR
    invalid_payload["vpcs"][0]["subnets"][0][
        "cidr"
    ] = "172.16.1.0/24"  # Assign the invalid CIDR block

    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_empty_tag(client: TestClient) -> None:
    """Test for a 422 response when a tag is empty."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0]["tags"].append("")
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_provider(client: TestClient) -> None:
    """Test for a 422 response when the provider is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["provider"] = "invalid_provider"  # Not a valid enum value
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_hostname(client: TestClient) -> None:
    """Test for a 422 response when a hostname is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpcs"][0]["subnets"][0]["hosts"][0]["hostname"] = "-i-am-invalid"
    response = client.post(f"{BASE_ROUTE}/templates/ranges", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

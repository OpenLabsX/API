import copy
import uuid
from typing import Any

from fastapi import status
from fastapi.testclient import TestClient

from src.app.main import app

from .config import BASE_ROUTE

client = TestClient(app)

###### Test /template/range #######

# Valid payload for comparison
valid_range_payload: dict[str, Any] = {
    "vpc": {
        "cidr": "192.168.0.0/16",
        "name": "example-vpc-1",
        "subnets": [
            {
                "cidr": "192.168.1.0/24",
                "name": "example-subnet-1",
                "hosts": [
                    {
                        "hostname": "example-host-1",
                        "spec": "tiny",
                        "os": "debian_11",
                        "size": 1,
                        "tags": ["web", "linux"],
                    }
                ],
            }
        ],
    },
    "provider": "aws",
    "vnc": False,
    "vpn": False,
}

valid_range_payload_yaml: str = """provider: aws
vnc: false
vpc:
  cidr: 192.168.0.0/16
  name: example-vpc-1
  subnets:
  - cidr: 192.168.1.0/24
    hosts:
    - hostname: example-host-1
      os: debian_11
      size: 1
      spec: tiny
      tags:
      - web
      - linux
    name: example-subnet-1
vpn: false
"""


def test_template_range_valid_payload_json() -> None:
    """Test that we get a 200 and a valid uuid.UUID4 in response."""
    response = client.post(f"{BASE_ROUTE}/templates/range", json=valid_range_payload)
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


def test_template_range_valid_payload_yaml() -> None:
    """Test that we get a 200 and a valid uuid.UUID4 in response."""
    response = client.post(
        f"{BASE_ROUTE}/templates/range",
        content=valid_range_payload_yaml,
        headers={"content-type": "application/yaml"},
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["id"]

    # Validate UUID returned
    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


def test_template_range_invalid_vpc_cidr() -> None:
    """Test for 422 response when VPC CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpc"]["cidr"] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_subnet_cidr() -> None:
    """Test for 422 response when subnet CIDR is invalid."""
    # Use deepcopy to ensure all nested dicts are copied
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpc"]["subnets"][
        0
    ] = "192.168.300.0/24"  # Assign the invalid CIDR block
    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_vpc_subnet_cidr_contain() -> None:
    """Test for 422 response when subnet CIDR is not contained in the VPC CIDR."""
    invalid_payload = copy.deepcopy(valid_range_payload)

    # VPC CIDR
    invalid_payload["vpc"]["cidr"] = "192.168.0.0/16"

    # Subnet CIDR
    invalid_payload["vpc"]["subnets"][0][
        "cidr"
    ] = "172.16.1.0/24"  # Assign the invalid CIDR block

    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_empty_tag() -> None:
    """Test for a 422 response when a tag is empty."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpc"]["subnets"][0]["hosts"][0]["tags"].append("")
    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_provider() -> None:
    """Test for a 422 response when the provider is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["provider"] = "invalid_provider"  # Not a valid enum value
    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_template_range_invalid_hostname() -> None:
    """Test for a 422 response when a hostname is invalid."""
    invalid_payload = copy.deepcopy(valid_range_payload)
    invalid_payload["vpc"]["subnets"][0]["hosts"][0]["hostname"] = "-i-am-invalid"
    response = client.post(f"{BASE_ROUTE}/templates/range", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

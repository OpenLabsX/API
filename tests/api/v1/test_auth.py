from .config import BASE_ROUTE
import uuid
import copy

from httpx import AsyncClient

from fastapi import status


user_register_payload = {
    "email": "test-auth@ufsit.club",
    "password": "password123",
    "name": "Adam Hassan",
}

user_login_payload = copy.deepcopy(user_register_payload)
user_login_payload.pop("name")


async def test_user_register(client: AsyncClient) -> None:
    """Test that we get a 200 response when registering a user."""
    response = await client.post(
        f"{BASE_ROUTE}/auth/register", json=user_register_payload
    )
    assert response.status_code == status.HTTP_200_OK

    uuid_response = response.json()["id"]
    uuid_obj = uuid.UUID(uuid_response, version=4)
    assert str(uuid_obj) == uuid_response


async def test_duplicate_user_register(client: AsyncClient) -> None:
    """Test that we get a 400 response when registering a user with the same email."""
    response = await client.post(
        f"{BASE_ROUTE}/auth/register", json=user_register_payload
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response_json = response.json()
    assert response_json["detail"] == "User already exists"


async def test_duplicate_user_diff_name_pass_register(client: AsyncClient) -> None:
    """Test that we get a 400 response when registering a user with the same email but a different password and name."""

    new_user_register_payload = copy.deepcopy(user_register_payload)
    new_user_register_payload["password"] = "newpassword123"
    new_user_register_payload["name"] = "New Name"

    response = await client.post(
        f"{BASE_ROUTE}/auth/register", json=user_register_payload
    )
    assert response.status_code == status.HTTP_409_CONFLICT

    response_json = response.json()
    assert response_json["detail"] == "User already exists"


async def test_user_register_invalid_payload(client: AsyncClient) -> None:
    """Test that we get a 422 response when registering a user with an invalid payload."""
    invalid_payload = copy.deepcopy(user_register_payload)
    invalid_payload.pop("email")

    response = await client.post(f"{BASE_ROUTE}/auth/register", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    invalid_payload = copy.deepcopy(user_register_payload)
    invalid_payload.pop("password")

    response = await client.post(f"{BASE_ROUTE}/auth/register", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    invalid_payload = copy.deepcopy(user_register_payload)
    invalid_payload.pop("name")

    response = await client.post(f"{BASE_ROUTE}/auth/register", json=invalid_payload)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


async def test_user_login_correct_pass(client: AsyncClient) -> None:
    """Test that we get a 200 response when logging in a user and get a valid JWT."""
    response = await client.post(f"{BASE_ROUTE}/auth/login", json=user_login_payload)
    assert response.status_code == status.HTTP_200_OK

    jwt = response.json()["token"]
    assert jwt


async def test_user_login_incorrect_pass(client: AsyncClient) -> None:
    """Test that we get a 401 response when logging in a user with an incorrect password."""
    invalid_payload = copy.deepcopy(user_login_payload)
    invalid_payload["password"] = "incorrectpassword"

    response = await client.post(f"{BASE_ROUTE}/auth/login", json=invalid_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


async def test_nonexistent_user_login(client: AsyncClient) -> None:
    """Test that we get a 401 response when logging in a user that doesn't exist."""
    invalid_payload = copy.deepcopy(user_login_payload)
    invalid_payload["email"] = "alex@ufsit.club"

    response = await client.post(f"{BASE_ROUTE}/auth/login", json=invalid_payload)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

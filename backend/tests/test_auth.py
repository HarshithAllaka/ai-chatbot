import pytest


@pytest.mark.asyncio
async def test_signup(client):
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": "john@example.com",
            "full_name": "John Doe",
            "password": "Password123",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["email"] == "john@example.com"
    assert data["full_name"] == "John Doe"

    assert "id" in data

    assert "hashed_password" not in data
    assert "password" not in data
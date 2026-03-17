import pytest
from fastapi.testclient import TestClient

def test_create_user(client: TestClient):
    response = client.post(
        "/users/",
        json={"username": "testuser", "email": "testuser@example.com", "password": "testpassword"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == "testuser"
    assert "id" in data

def test_login_for_access_token(client: TestClient):
    client.post(
        "/users/",
        json={"username": "testauth", "email": "testauth@example.com", "password": "password123"}
    )
    response = client.post(
        "/token",
        data={"username": "testauth", "password": "password123"}
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_read_users_me(client: TestClient):
    # First create and get token
    client.post(
        "/users/",
        json={"username": "testme", "email": "testme@example.com", "password": "password"}
    )
    response = client.post(
        "/token",
        data={"username": "testme", "password": "password"}
    )
    token = response.json().get("access_token")

    # Access protected route
    headers = {"Authorization": f"Bearer {token}"}
    me_response = client.get("/users/me/", headers=headers)
    assert me_response.status_code == 200
    assert me_response.json()["username"] == "testme"

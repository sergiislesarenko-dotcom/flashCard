import pytest
from fastapi.testclient import TestClient

from tests.conftest import auth_headers, login_user, make_language, register_user


def test_register_success(client: TestClient, db):
    resp = client.post("/auth/register", json={
        "email": "new@example.com",
        "password": "secret123",
        "display_name": "New User",
    })
    assert resp.status_code == 201
    body = resp.json()
    assert body["email"] == "new@example.com"
    assert body["displayName"] == "New User"
    assert "id" in body
    assert "password_hash" not in body


def test_register_duplicate_email(client: TestClient, db):
    register_user(client)
    resp = client.post("/auth/register", json={
        "email": "test@example.com",
        "password": "password123",
        "display_name": "Another",
    })
    assert resp.status_code == 409


def test_register_short_password(client: TestClient, db):
    resp = client.post("/auth/register", json={
        "email": "short@example.com",
        "password": "abc",
        "display_name": "User",
    })
    assert resp.status_code == 422


def test_login_success(client: TestClient, db):
    register_user(client)
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert "accessToken" in resp.json()


def test_login_wrong_password(client: TestClient, db):
    register_user(client)
    resp = client.post("/auth/login", json={"email": "test@example.com", "password": "wrongpassword"})
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient, db):
    resp = client.post("/auth/login", json={"email": "nobody@example.com", "password": "password123"})
    assert resp.status_code == 401


def test_protected_route_requires_auth(client: TestClient, db):
    resp = client.get("/sets")
    assert resp.status_code == 401


def test_protected_route_with_token(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/sets", headers=auth_headers(token))
    assert resp.status_code == 200


def test_logout(client: TestClient, db):
    register_user(client)
    # login to get cookie
    client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    resp = client.post("/auth/logout")
    assert resp.status_code == 204


def test_refresh_without_cookie(client: TestClient, db):
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401

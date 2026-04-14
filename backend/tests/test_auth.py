from fastapi.testclient import TestClient

from tests.conftest import auth_headers, login_user, register_user


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


def test_register_missing_display_name(client: TestClient, db):
    resp = client.post("/auth/register", json={
        "email": "x@example.com",
        "password": "password123",
    })
    assert resp.status_code == 422


def test_login_success(client: TestClient, db):
    register_user(client)
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert resp.status_code == 200
    assert "accessToken" in resp.json()


def test_login_response_shape(client: TestClient, db):
    register_user(client)
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    body = resp.json()
    assert "accessToken" in body
    assert "user" in body
    assert body["user"]["email"] == "test@example.com"


def test_login_wrong_password(client: TestClient, db):
    register_user(client)
    resp = client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "wrongpassword"},
    )
    assert resp.status_code == 401


def test_login_unknown_email(client: TestClient, db):
    resp = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "password123"},
    )
    assert resp.status_code == 401


def test_login_sets_refresh_cookie(client: TestClient, db):
    register_user(client)
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    assert "refresh_token" in client.cookies


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
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    resp = client.post("/auth/logout")
    assert resp.status_code == 204


def test_refresh_without_cookie(client: TestClient, db):
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401


def test_refresh_valid_cookie(client: TestClient, db):
    """Login sets refresh cookie; /auth/refresh returns a new access token."""
    register_user(client)
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    resp = client.post("/auth/refresh")
    assert resp.status_code == 200
    assert "accessToken" in resp.json()


def test_refresh_token_rotation(client: TestClient, db):
    """After refresh, the rotated cookie can be used for another refresh."""
    register_user(client)
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    resp1 = client.post("/auth/refresh")
    assert resp1.status_code == 200
    resp2 = client.post("/auth/refresh")
    assert resp2.status_code == 200
    assert "accessToken" in resp2.json()


def test_logout_invalidates_refresh_token(client: TestClient, db):
    """After logout, the refresh cookie can no longer be used."""
    register_user(client)
    client.post(
        "/auth/login",
        json={"email": "test@example.com", "password": "password123"},
    )
    client.post("/auth/logout")
    resp = client.post("/auth/refresh")
    assert resp.status_code == 401

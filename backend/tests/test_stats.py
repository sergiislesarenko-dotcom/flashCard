from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_set, login_user, make_language, register_user


def test_overview_empty(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["totalSets"] == 0
    assert body["totalCards"] == 0
    assert body["dueToday"] == 0
    assert body["sessionsCompleted"] == 0
    assert body["streakDays"] == 0


def test_overview_counts_sets_and_cards(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post("/cards", json={"set_id": fset["id"], "front": "A", "back": "B"}, headers=auth_headers(token))
    client.post("/cards", json={"set_id": fset["id"], "front": "C", "back": "D"}, headers=auth_headers(token))

    resp = client.get("/stats/overview", headers=auth_headers(token))
    body = resp.json()
    assert body["totalSets"] == 1
    assert body["totalCards"] == 2


def test_progress_empty(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/stats/progress", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_stats_isolated_per_user(client: TestClient, db):
    """User A's stats don't leak to User B."""
    lang = make_language(db)

    register_user(client, email="a@example.com")
    token_a = login_user(client, email="a@example.com")
    fset = create_set(client, token_a, lang.id, name="A's Set")
    client.post("/cards", json={"set_id": fset["id"], "front": "X", "back": "Y"}, headers=auth_headers(token_a))

    register_user(client, email="b@example.com")
    token_b = login_user(client, email="b@example.com")
    resp = client.get("/stats/overview", headers=auth_headers(token_b))
    body = resp.json()
    assert body["totalSets"] == 0
    assert body["totalCards"] == 0

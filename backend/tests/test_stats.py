from fastapi.testclient import TestClient

from tests.conftest import (
    auth_headers, create_set, login_user, make_language, register_user,
)


def _run_session(client, token, fset, result="remembered"):
    """Create a 1-card session, review it, complete it. Returns summary."""
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]
    card_id = body["cards"][0]["id"]
    client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card_id, "result": result},
        headers=auth_headers(token),
    )
    return client.post(
        f"/learning/sessions/{session_id}/complete",
        headers=auth_headers(token),
    ).json()


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
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "C", "back": "D"},
        headers=auth_headers(token),
    )
    resp = client.get("/stats/overview", headers=auth_headers(token))
    body = resp.json()
    assert body["totalSets"] == 1
    assert body["totalCards"] == 2


def test_overview_due_today(client: TestClient, db):
    """Cards are created with next_review_at=now → immediately due."""
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "C", "back": "D"},
        headers=auth_headers(token),
    )
    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.json()["dueToday"] == 2


def test_overview_sessions_completed(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    _run_session(client, token, fset)

    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.json()["sessionsCompleted"] == 1


def test_overview_average_accuracy_100(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    _run_session(client, token, fset, result="remembered")

    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.json()["averageAccuracy"] == 100.0


def test_overview_average_accuracy_mixed(client: TestClient, db):
    """Two sessions: 100% and 0% → averageAccuracy == 50.0."""
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    # Need 2 cards so each session can pick a different card
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "C", "back": "D"},
        headers=auth_headers(token),
    )
    _run_session(client, token, fset, result="remembered")
    _run_session(client, token, fset, result="repeat")

    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.json()["averageAccuracy"] == 50.0


def test_overview_streak_single_day(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    _run_session(client, token, fset)

    resp = client.get("/stats/overview", headers=auth_headers(token))
    assert resp.json()["streakDays"] == 1


def test_progress_empty(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/stats/progress", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_progress_with_completed_session(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    _run_session(client, token, fset)

    resp = client.get("/stats/progress", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["sessionsCompleted"] == 1
    assert data[0]["cardsReviewed"] == 1
    assert data[0]["cardsRemembered"] == 1


def test_stats_isolated_per_user(client: TestClient, db):
    """User A's stats don't leak to User B."""
    lang = make_language(db)

    register_user(client, email="a@example.com")
    token_a = login_user(client, email="a@example.com")
    fset = create_set(client, token_a, lang.id, name="A's Set")
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "X", "back": "Y"},
        headers=auth_headers(token_a),
    )

    register_user(client, email="b@example.com")
    token_b = login_user(client, email="b@example.com")
    resp = client.get("/stats/overview", headers=auth_headers(token_b))
    body = resp.json()
    assert body["totalSets"] == 0
    assert body["totalCards"] == 0

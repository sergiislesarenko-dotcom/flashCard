from fastapi.testclient import TestClient

from tests.conftest import (
    auth_headers, create_set, login_user, make_language, register_user,
)


def _setup_with_cards(client, db, num_cards=3):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    for i in range(num_cards):
        client.post(
            "/cards",
            json={"set_id": fset["id"], "front": f"Word {i}", "back": f"T{i}"},
            headers=auth_headers(token),
        )
    return token, fset


def test_create_session(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=3)
    resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 3},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert "sessionId" in body
    assert body["setId"] == fset["id"]
    assert len(body["cards"]) == 3
    assert body["totalCards"] == 3
    for card in body["cards"]:
        assert "front" in card
        assert "back" in card


def test_create_session_wrong_set(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/learning/sessions",
        json={"set_id": 9999, "card_count": 5},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


def test_create_session_all_cards(client: TestClient, db):
    """card_count omitted → all cards in the set are returned."""
    token, fset = _setup_with_cards(client, db, num_cards=5)
    resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"]},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["totalCards"] == 5
    assert len(body["cards"]) == 5


def test_session_response_includes_language_code(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
    resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["languageCode"] == "ru"


def test_get_session(client: TestClient, db):
    token, fset = _setup_with_cards(client, db)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 3},
        headers=auth_headers(token),
    )
    session_id = session_resp.json()["sessionId"]
    resp = client.get(
        f"/learning/sessions/{session_id}",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["sessionId"] == session_id
    assert resp.json()["status"] == "active"


def test_get_session_not_found(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/learning/sessions/9999", headers=auth_headers(token))
    assert resp.status_code == 404


def test_get_session_wrong_user(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    fset = create_set(client, token1, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token1),
    )
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token1),
    )
    session_id = session_resp.json()["sessionId"]

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.get(
        f"/learning/sessions/{session_id}",
        headers=auth_headers(token2),
    )
    assert resp.status_code == 403


def test_submit_review_remembered(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]
    card_id = body["cards"][0]["id"]

    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card_id, "result": "remembered"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["result"] == "remembered"
    assert result["intervalDays"] == 1
    assert result["repetitions"] == 1


def test_submit_review_repeat(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]
    card_id = body["cards"][0]["id"]

    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card_id, "result": "repeat"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    result = resp.json()
    assert result["result"] == "repeat"
    assert result["intervalDays"] == 1
    assert result["repetitions"] == 0


def test_submit_review_invalid_result(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]
    card_id = body["cards"][0]["id"]
    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card_id, "result": "unknown"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422


def test_submit_review_card_not_found(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    session_id = session_resp.json()["sessionId"]
    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": 9999, "result": "remembered"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


def test_submit_review_card_from_wrong_set(client: TestClient, db):
    """Card from a different set than the session's set is rejected."""
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    set1 = create_set(client, token, lang.id, name="Set 1")
    set2 = create_set(client, token, lang.id, name="Set 2")

    client.post(
        "/cards",
        json={"set_id": set1["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    card2_resp = client.post(
        "/cards",
        json={"set_id": set2["id"], "front": "C", "back": "D"},
        headers=auth_headers(token),
    )
    card2_id = card2_resp.json()["id"]

    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": set1["id"], "card_count": 1},
        headers=auth_headers(token),
    )
    session_id = session_resp.json()["sessionId"]

    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card2_id, "result": "remembered"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 403


def test_duplicate_review_rejected(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
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
        json={"card_id": card_id, "result": "remembered"},
        headers=auth_headers(token),
    )
    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": card_id, "result": "repeat"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409


def test_complete_session(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=1)
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
        json={"card_id": card_id, "result": "remembered"},
        headers=auth_headers(token),
    )
    resp = client.post(
        f"/learning/sessions/{session_id}/complete",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["status"] == "completed"
    assert summary["cardsReviewed"] == 1
    assert summary["cardsRemembered"] == 1
    assert summary["accuracyPercent"] == 100


def test_complete_session_not_found(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/learning/sessions/9999/complete",
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


def test_complete_session_wrong_user(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    fset = create_set(client, token1, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token1),
    )
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 1},
        headers=auth_headers(token1),
    )
    session_id = session_resp.json()["sessionId"]

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.post(
        f"/learning/sessions/{session_id}/complete",
        headers=auth_headers(token2),
    )
    assert resp.status_code == 403


def test_complete_session_zero_reviews_accuracy(client: TestClient, db):
    """Complete with no reviews → accuracyPercent=0, no division error."""
    token, fset = _setup_with_cards(client, db, num_cards=2)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 2},
        headers=auth_headers(token),
    )
    session_id = session_resp.json()["sessionId"]
    resp = client.post(
        f"/learning/sessions/{session_id}/complete",
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["accuracyPercent"] == 0
    assert body["cardsReviewed"] == 0


def test_review_on_completed_session_rejected(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=2)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 2},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]

    client.post(
        f"/learning/sessions/{session_id}/complete",
        headers=auth_headers(token),
    )
    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": body["cards"][0]["id"], "result": "remembered"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409

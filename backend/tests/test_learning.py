from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_set, login_user, make_language, register_user


def _setup_with_cards(client, db, num_cards=3):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    for i in range(num_cards):
        client.post(
            "/cards",
            json={"set_id": fset["id"], "front": f"Word {i}", "back": f"Translation {i}"},
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
    # Cards must have front and back
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


def test_get_session(client: TestClient, db):
    token, fset = _setup_with_cards(client, db)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 3},
        headers=auth_headers(token),
    )
    session_id = session_resp.json()["sessionId"]
    resp = client.get(f"/learning/sessions/{session_id}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["sessionId"] == session_id
    assert resp.json()["status"] == "active"


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
    assert result["intervalDays"] == 1  # first review → interval 1
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
    resp = client.post(f"/learning/sessions/{session_id}/complete", headers=auth_headers(token))
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["status"] == "completed"
    assert summary["cardsReviewed"] == 1
    assert summary["cardsRemembered"] == 1
    assert summary["accuracyPercent"] == 100


def test_review_on_completed_session_rejected(client: TestClient, db):
    token, fset = _setup_with_cards(client, db, num_cards=2)
    session_resp = client.post(
        "/learning/sessions",
        json={"set_id": fset["id"], "card_count": 2},
        headers=auth_headers(token),
    )
    body = session_resp.json()
    session_id = body["sessionId"]

    client.post(f"/learning/sessions/{session_id}/complete", headers=auth_headers(token))

    resp = client.post(
        f"/learning/sessions/{session_id}/reviews",
        json={"card_id": body["cards"][0]["id"], "result": "remembered"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 409

from fastapi.testclient import TestClient

from tests.conftest import auth_headers, create_set, login_user, make_language, register_user


def _setup(client, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    return token, fset


def test_list_cards_empty(client: TestClient, db):
    token, fset = _setup(client, db)
    resp = client.get(f"/cards?set_id={fset['id']}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_card(client: TestClient, db):
    token, fset = _setup(client, db)
    resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "Привет", "back": "Hello"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["front"] == "Привет"
    assert body["back"] == "Hello"
    assert body["easeFactor"] is not None


def test_create_card_increments_card_count(client: TestClient, db):
    token, fset = _setup(client, db)
    client.post("/cards", json={"set_id": fset["id"], "front": "A", "back": "B"}, headers=auth_headers(token))
    resp = client.get(f"/sets/{fset['id']}", headers=auth_headers(token))
    assert resp.json()["cardCount"] == 1


def test_import_cards(client: TestClient, db):
    token, fset = _setup(client, db)
    resp = client.post(
        "/cards/import",
        json={"set_id": fset["id"], "cards": [
            {"front": "Кот", "back": "Cat"},
            {"front": "Собака", "back": "Dog"},
        ]},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    assert len(resp.json()) == 2


def test_import_increments_card_count(client: TestClient, db):
    token, fset = _setup(client, db)
    client.post(
        "/cards/import",
        json={"set_id": fset["id"], "cards": [
            {"front": "A", "back": "B"},
            {"front": "C", "back": "D"},
            {"front": "E", "back": "F"},
        ]},
        headers=auth_headers(token),
    )
    resp = client.get(f"/sets/{fset['id']}", headers=auth_headers(token))
    assert resp.json()["cardCount"] == 3


def test_update_card(client: TestClient, db):
    token, fset = _setup(client, db)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "Old", "back": "Old Back"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.patch(f"/cards/{card_id}", json={"front": "New"}, headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["front"] == "New"
    assert resp.json()["back"] == "Old Back"


def test_delete_card(client: TestClient, db):
    token, fset = _setup(client, db)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.delete(f"/cards/{card_id}", headers=auth_headers(token))
    assert resp.status_code == 204
    # card_count decremented
    set_resp = client.get(f"/sets/{fset['id']}", headers=auth_headers(token))
    assert set_resp.json()["cardCount"] == 0


def test_card_access_requires_ownership(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    fset = create_set(client, token1, lang.id)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token1),
    )
    card_id = card_resp.json()["id"]

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.get(f"/cards?set_id={fset['id']}", headers=auth_headers(token2))
    assert resp.status_code == 403

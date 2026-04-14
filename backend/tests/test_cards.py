from fastapi.testclient import TestClient

from app import models
from tests.conftest import (
    auth_headers, create_set, login_user, make_language, register_user,
)


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
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    resp = client.get(f"/sets/{fset['id']}", headers=auth_headers(token))
    assert resp.json()["cardCount"] == 1


def test_create_card_empty_front(client: TestClient, db):
    token, fset = _setup(client, db)
    resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "", "back": "B"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422


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


def test_import_into_wrong_set(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    fset = create_set(client, token1, lang.id)

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.post(
        "/cards/import",
        json={"set_id": fset["id"], "cards": [{"front": "A", "back": "B"}]},
        headers=auth_headers(token2),
    )
    assert resp.status_code == 403


def test_update_card(client: TestClient, db):
    token, fset = _setup(client, db)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "Old", "back": "Old Back"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.patch(
        f"/cards/{card_id}",
        json={"front": "New"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["front"] == "New"
    assert resp.json()["back"] == "Old Back"


def test_update_card_wrong_user(client: TestClient, db):
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
    resp = client.patch(
        f"/cards/{card_id}",
        json={"front": "Hacked"},
        headers=auth_headers(token2),
    )
    assert resp.status_code == 403


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
    set_resp = client.get(f"/sets/{fset['id']}", headers=auth_headers(token))
    assert set_resp.json()["cardCount"] == 0


def test_delete_card_wrong_user(client: TestClient, db):
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
    resp = client.delete(f"/cards/{card_id}", headers=auth_headers(token2))
    assert resp.status_code == 403


def test_card_access_requires_ownership(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    fset = create_set(client, token1, lang.id)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token1),
    )
    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.get(f"/cards?set_id={fset['id']}", headers=auth_headers(token2))
    assert resp.status_code == 403


def test_list_all_cards(client: TestClient, db):
    token, fset = _setup(client, db)
    client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    resp = client.get("/cards/all", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["pagination"]["total"] == 1
    assert len(body["data"]) == 1


def test_list_all_cards_deduplication(client: TestClient, db):
    """Same front+back in two sets → counted once in /cards/all."""
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    set1 = create_set(client, token, lang.id, name="Set 1")
    set2 = create_set(client, token, lang.id, name="Set 2")
    client.post(
        "/cards",
        json={"set_id": set1["id"], "front": "Same", "back": "Same"},
        headers=auth_headers(token),
    )
    client.post(
        "/cards",
        json={"set_id": set2["id"], "front": "Same", "back": "Same"},
        headers=auth_headers(token),
    )
    client.post(
        "/cards",
        json={"set_id": set1["id"], "front": "Unique", "back": "Unique"},
        headers=auth_headers(token),
    )
    resp = client.get("/cards/all", headers=auth_headers(token))
    assert resp.json()["pagination"]["total"] == 2


def test_list_all_cards_pagination(client: TestClient, db):
    token, fset = _setup(client, db)
    for i in range(5):
        client.post(
            "/cards",
            json={"set_id": fset["id"], "front": f"W{i}", "back": f"B{i}"},
            headers=auth_headers(token),
        )
    resp = client.get("/cards/all?page=1&pageSize=2", headers=auth_headers(token))
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 5


def test_get_card_examples_empty(client: TestClient, db):
    token, fset = _setup(client, db)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "Word", "back": "Trans"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.get(f"/cards/{card_id}/examples", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []


def test_get_card_examples_with_data(client: TestClient, db):
    token, fset = _setup(client, db)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "Word", "back": "Trans"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    example = models.CardExample(card_id=card_id, text="Example sentence")
    db.add(example)
    db.commit()

    resp = client.get(f"/cards/{card_id}/examples", headers=auth_headers(token))
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["text"] == "Example sentence"
    assert data[0]["cardId"] == card_id


def test_get_card_examples_wrong_user(client: TestClient, db):
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
    resp = client.get(f"/cards/{card_id}/examples", headers=auth_headers(token2))
    assert resp.status_code == 403

from fastapi.testclient import TestClient

from tests.conftest import (
    auth_headers, create_set, login_user, make_language, register_user,
)


def test_list_sets_empty(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/sets", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["data"] == []
    assert body["pagination"]["total"] == 0


def test_create_set(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/sets",
        json={"name": "Russian Basics", "language_id": lang.id},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "Russian Basics"
    assert body["cardCount"] == 0
    assert body["language"]["code"] == "ru"


def test_create_set_invalid_language(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/sets",
        json={"name": "Test", "language_id": 999},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


def test_get_set(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    created = create_set(client, token, lang.id)
    resp = client.get(f"/sets/{created['id']}", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_set_not_found(client: TestClient, db):
    register_user(client)
    token = login_user(client)
    resp = client.get("/sets/9999", headers=auth_headers(token))
    assert resp.status_code == 404


def test_get_set_wrong_user(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    created = create_set(client, token1, lang.id)

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.get(f"/sets/{created['id']}", headers=auth_headers(token2))
    assert resp.status_code == 403


def test_update_set(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    created = create_set(client, token, lang.id)
    resp = client.patch(
        f"/sets/{created['id']}",
        json={"name": "Updated Name"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["name"] == "Updated Name"


def test_delete_set(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    created = create_set(client, token, lang.id)
    resp = client.delete(f"/sets/{created['id']}", headers=auth_headers(token))
    assert resp.status_code == 204
    # Verify gone
    resp = client.get(f"/sets/{created['id']}", headers=auth_headers(token))
    assert resp.status_code == 404


def test_list_sets_pagination_shape(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    create_set(client, token, lang.id, name="Set A")
    create_set(client, token, lang.id, name="Set B")
    resp = client.get("/sets", headers=auth_headers(token))
    body = resp.json()
    assert len(body["data"]) == 2
    assert body["pagination"]["total"] == 2


def test_create_set_with_description(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/sets",
        json={"name": "Described", "description": "A desc", "language_id": lang.id},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    assert resp.json()["description"] == "A desc"


def test_update_set_description(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    created = create_set(client, token, lang.id)
    resp = client.patch(
        f"/sets/{created['id']}",
        json={"description": "New desc"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    assert resp.json()["description"] == "New desc"


def test_update_set_wrong_user(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    created = create_set(client, token1, lang.id)

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.patch(
        f"/sets/{created['id']}",
        json={"name": "Hacked"},
        headers=auth_headers(token2),
    )
    assert resp.status_code == 403


def test_delete_set_wrong_user(client: TestClient, db):
    lang = make_language(db)
    register_user(client, email="owner@example.com")
    token1 = login_user(client, email="owner@example.com")
    created = create_set(client, token1, lang.id)

    register_user(client, email="other@example.com")
    token2 = login_user(client, email="other@example.com")
    resp = client.delete(f"/sets/{created['id']}", headers=auth_headers(token2))
    assert resp.status_code == 403


def test_create_set_empty_name(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/sets",
        json={"name": "   ", "language_id": lang.id},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422


def test_create_set_from_cards(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.post(
        "/sets/from-cards",
        json={"name": "New Set", "language_id": lang.id, "card_ids": [card_id]},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "New Set"
    assert body["cardCount"] == 1


def test_create_set_from_cards_other_user_card(client: TestClient, db):
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
    resp = client.post(
        "/sets/from-cards",
        json={"name": "Stolen", "language_id": lang.id, "card_ids": [card_id]},
        headers=auth_headers(token2),
    )
    assert resp.status_code == 400


def test_create_set_from_cards_invalid_language(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    fset = create_set(client, token, lang.id)
    card_resp = client.post(
        "/cards",
        json={"set_id": fset["id"], "front": "A", "back": "B"},
        headers=auth_headers(token),
    )
    card_id = card_resp.json()["id"]
    resp = client.post(
        "/sets/from-cards",
        json={"name": "Bad", "language_id": 9999, "card_ids": [card_id]},
        headers=auth_headers(token),
    )
    assert resp.status_code == 404


def test_create_set_from_cards_empty_list(client: TestClient, db):
    lang = make_language(db)
    register_user(client)
    token = login_user(client)
    resp = client.post(
        "/sets/from-cards",
        json={"name": "Empty", "language_id": lang.id, "card_ids": []},
        headers=auth_headers(token),
    )
    assert resp.status_code == 422

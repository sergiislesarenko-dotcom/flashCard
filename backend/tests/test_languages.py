from fastapi.testclient import TestClient

from tests.conftest import make_language


def test_list_languages_empty(client: TestClient, db):
    resp = client.get("/languages")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_languages_returns_all(client: TestClient, db):
    make_language(db, code="ru", name="Russian", flag="🇷🇺")
    make_language(db, code="de", name="German", flag="🇩🇪")
    resp = client.get("/languages")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = [d["name"] for d in data]
    assert "Russian" in names
    assert "German" in names


def test_languages_are_public(client: TestClient, db):
    """No auth token required."""
    make_language(db)
    resp = client.get("/languages")
    assert resp.status_code == 200


def test_language_response_shape(client: TestClient, db):
    make_language(db, code="ru", name="Russian", flag="🇷🇺")
    resp = client.get("/languages")
    item = resp.json()[0]
    assert "id" in item
    assert item["code"] == "ru"
    assert item["name"] == "Russian"
    assert item["flag"] == "🇷🇺"

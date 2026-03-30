import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.dependencies import get_current_user
from app import models
from main import app

engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(autouse=True)
def setup_db():
    """Create all tables before each test, drop after."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=True)


@pytest.fixture
def db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def make_language(db, code="ru", name="Russian", flag="🇷🇺") -> models.Language:
    lang = models.Language(code=code, name=name, flag=flag)
    db.add(lang)
    db.commit()
    db.refresh(lang)
    return lang


def register_user(client: TestClient, email="test@example.com", password="password123", display_name="Test User") -> dict:
    resp = client.post("/auth/register", json={"email": email, "password": password, "display_name": display_name})
    assert resp.status_code == 201
    return resp.json()


def login_user(client: TestClient, email="test@example.com", password="password123") -> str:
    resp = client.post("/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200
    return resp.json()["accessToken"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


def create_set(client: TestClient, token: str, language_id: int, name="My Set") -> dict:
    resp = client.post(
        "/sets",
        json={"name": name, "language_id": language_id},
        headers=auth_headers(token),
    )
    assert resp.status_code == 201
    return resp.json()

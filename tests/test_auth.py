import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import deps
from app.core.config import _environment_file, settings
from app.db.session import Base
from app.main import app


@pytest.mark.parametrize(
    ("environment", "expected_file"),
    [
        ("development", ".env.development"),
        ("qa", ".env.qa"),
        ("production", ".env.production"),
    ],
)
def test_environment_file_matches_app_env(
    monkeypatch: pytest.MonkeyPatch, environment: str, expected_file: str
) -> None:
    monkeypatch.setenv("APP_ENV", environment)

    assert _environment_file() == expected_file


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )
    monkeypatch.setattr("app.main.engine", engine)
    monkeypatch.setattr(deps, "SessionLocal", TestingSessionLocal)
    with TestClient(app) as test_client:
        yield test_client
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


def register(client: TestClient, email: str = "jordan@example.com") -> dict:
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Jordan Lee",
            "email": email,
            "password": "safe-password-123",
        },
    )
    assert response.status_code == 201
    return response.json()


def test_registration_login_and_current_user(client: TestClient) -> None:
    user = register(client)
    assert user["email"] == "jordan@example.com"
    assert user["role"] == "employee"
    assert "hashed_password" not in user

    login = client.post(
        "/api/auth/login",
        json={"email": "jordan@example.com", "password": "safe-password-123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    current_user = client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert current_user.status_code == 200
    assert current_user.json()["id"] == user["id"]


def test_registration_rejects_duplicate_email(client: TestClient) -> None:
    register(client)
    response = client.post(
        "/api/auth/register",
        json={
            "full_name": "Another User",
            "email": "JORDAN@example.com",
            "password": "safe-password-123",
        },
    )
    assert response.status_code == 409


def test_login_and_user_routes_require_valid_authentication(client: TestClient) -> None:
    register(client)
    bad_login = client.post(
        "/api/auth/login",
        json={"email": "jordan@example.com", "password": "wrong-password"},
    )
    assert bad_login.status_code == 401
    assert client.get("/api/users/me").status_code == 401


@pytest.mark.parametrize("origin", settings.allowed_origins)
def test_registration_preflight_allows_configured_origins(
    client: TestClient, origin: str
) -> None:
    response = client.options(
        "/api/auth/register",
        headers={
            "Origin": origin,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin

import os

from fastapi.testclient import TestClient

from src.api import server


def test_auth_required_defaults_to_true_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)

    assert server._auth_required() is True


def test_auth_required_defaults_to_false_outside_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.delenv("AUTH_REQUIRED", raising=False)

    assert server._auth_required() is False


def test_api_key_must_be_explicit_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.delenv("API_KEY", raising=False)

    assert server._api_key() == ""


def test_health_endpoint_has_security_headers(monkeypatch):
    monkeypatch.setenv("APP_ENV", "development")
    monkeypatch.setenv("AUTH_REQUIRED", "false")

    with TestClient(server.app) as client:
        response = client.get("/health/live")

    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("cache-control") == "no-store"


def test_production_auth_enforced_for_protected_routes(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("API_KEY", "super-secret-key")

    with TestClient(server.app) as client:
        unauthorized = client.get("/v1/stream/status")
        authorized = client.get("/v1/stream/status", headers={"x-api-key": "super-secret-key"})

    assert unauthorized.status_code == 401
    assert unauthorized.json().get("detail") == "Unauthorized"
    assert authorized.status_code == 200


def test_production_allows_bearer_token_for_protected_routes(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.setenv("API_KEY", "super-secret-key")

    server._seed_staff_users()
    user = server._load_user_by_email("analyst@bank.local")
    assert user is not None
    token = server._issue_auth_token(user)

    with TestClient(server.app) as client:
        response = client.get(
            "/v1/stream/status",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200


def test_production_without_api_key_returns_service_error(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    monkeypatch.delenv("API_KEY", raising=False)

    with TestClient(server.app) as client:
        response = client.get("/v1/stream/status")

    assert response.status_code == 503
    assert "not configured" in str(response.json().get("detail", "")).lower()

import pytest
from fastapi.testclient import TestClient


def make_client(monkeypatch, tmp_path, **environment):
    from app.core.config import load_settings
    from app.main import create_app

    for name in ("GEOAPIFY_API_KEY", "GEOCODING_COUNTRY", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)
    for name, value in environment.items():
        monkeypatch.setenv(name, value)
    return TestClient(create_app(load_settings(tmp_path / "missing.env")))


def test_health_works_without_geoapify_key(monkeypatch, tmp_path):
    with make_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_public_endpoints_do_not_expose_secrets(monkeypatch, tmp_path):
    secret = "test-only-secret-not-a-real-key"
    with make_client(monkeypatch, tmp_path, GEOAPIFY_API_KEY=secret) as client:
        for path in ("/api/health", "/openapi.json", "/docs"):
            response = client.get(path)
            assert response.status_code == 200
            assert secret not in response.text


@pytest.mark.parametrize("origin", ["http://127.0.0.1:5500", "http://localhost:5500"])
def test_default_frontend_origins_can_read_health(monkeypatch, tmp_path, origin):
    with make_client(monkeypatch, tmp_path) as client:
        response = client.get("/api/health", headers={"Origin": origin})
    assert response.headers["access-control-allow-origin"] == origin


def test_other_origins_are_not_allowed(monkeypatch, tmp_path):
    with make_client(monkeypatch, tmp_path) as client:
        response = client.options(
            "/api/health",
            headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"},
        )
    assert response.status_code == 400
    assert "access-control-allow-origin" not in response.headers


def test_environment_can_replace_local_origins(monkeypatch, tmp_path):
    with make_client(monkeypatch, tmp_path, CORS_ORIGINS=" https://webgis.example ") as client:
        allowed = client.get("/api/health", headers={"Origin": "https://webgis.example"})
        denied = client.get("/api/health", headers={"Origin": "http://localhost:5500"})
    assert allowed.headers["access-control-allow-origin"] == "https://webgis.example"
    assert "access-control-allow-origin" not in denied.headers


def test_dotenv_loads_without_changing_process_environment(monkeypatch, tmp_path):
    from app.core.config import load_settings
    import os

    for name in ("GEOAPIFY_API_KEY", "GEOCODING_COUNTRY", "CORS_ORIGINS"):
        monkeypatch.delenv(name, raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text("GEOAPIFY_API_KEY=file-test-key\nGEOCODING_COUNTRY=vn\n", encoding="utf-8")
    settings = load_settings(env_file)
    assert settings.geoapify_api_key == "file-test-key"
    assert "file-test-key" not in repr(settings)
    assert "GEOAPIFY_API_KEY" not in os.environ
    monkeypatch.setenv("GEOAPIFY_API_KEY", "environment-test-key")
    assert load_settings(env_file).geoapify_api_key == "environment-test-key"


@pytest.mark.parametrize("origins", ["*", "null", "https://example.com/path", ""])
def test_invalid_cors_configuration_fails_closed(monkeypatch, tmp_path, origins):
    from app.core.config import load_settings

    monkeypatch.setenv("CORS_ORIGINS", origins)
    with pytest.raises(ValueError, match="CORS_ORIGINS"):
        load_settings(tmp_path / "missing.env")

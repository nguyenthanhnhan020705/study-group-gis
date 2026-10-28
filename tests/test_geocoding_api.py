from fastapi.testclient import TestClient
import httpx

from app.core.config import Settings
from app.main import create_app


def make_app(key=""):
    return create_app(Settings(cors_origins=("http://127.0.0.1:5500",), geoapify_api_key=key))


def test_missing_key_is_readable_without_calling_provider():
    with TestClient(make_app()) as client:
        response = client.post("/api/geocode/retry", json={"student_id": "S1", "address": "Đường A"})
    assert response.status_code == 503
    assert "chưa" in response.json()["message"].lower()


def test_batch_rejects_empty_duplicate_ids_and_large_payloads():
    with TestClient(make_app()) as client:
        for rows in [[], [{"student_id": "S1", "address": "A"}] * 2,
                     [{"student_id": str(i), "address": "A"} for i in range(6)]]:
            assert client.post("/api/geocode/batch", json={"students": rows}).status_code == 422
        assert client.post("/api/geocode/retry", json={"student_id": "S1", "address": " "}).status_code == 422


def test_retry_returns_candidates_without_verified_state():
    from app.services.geocoding_service import GeocodingService
    from dataclasses import replace
    app = make_app("test-secret")
    app.state.geocoding = GeocodingService(replace(app.state.settings, geocoding_interval=0), transport=httpx.MockTransport(
        lambda request: httpx.Response(200, json={"results": [{"lat": 10.85, "lon": 106.76, "formatted": "Đường A", "country_code": "vn", "result_type": "street", "rank": {"confidence": 0.9}}]})
    ))
    with TestClient(app) as client:
        response = client.post("/api/geocode/retry", json={"student_id": "S7", "address": "Đường A"})
    assert response.status_code == 200
    assert response.json()["student_id"] == "S7"
    assert response.json()["status"] == "needs_review"
    assert response.json()["candidates"][0]["eligible"]
    assert "test-secret" not in response.text

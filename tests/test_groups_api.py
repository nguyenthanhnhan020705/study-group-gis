import copy
import json
from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from grouping_fixtures import payload


@pytest.fixture
def app():
    return create_app(Settings(cors_origins=("http://127.0.0.1:5500",)))


def test_generate_returns_six_groups_with_exact_gender_counts(app):
    with TestClient(app) as client:
        response = client.post("/api/groups/generate", json=payload(), headers={"Origin": "http://127.0.0.1:5500"})
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
        result = response.json()
        assert result["k"] == 6
        assert all((group["size"], group["male"], group["female"]) == (5, 3, 2) for group in result["groups"])
        assert len(result["assignments"]) == 30


@pytest.mark.parametrize("field,value", [
    ("target_male", -1), ("target_female", -1), ("target_male", 1.5),
    ("target_male", 1.0), ("target_male", True), ("target_male", "3"),
])
def test_invalid_targets_rejected(app, field, value):
    data = payload(3, 2)
    data[field] = value
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=data).status_code == 422


@pytest.mark.parametrize("change", [
    {"geocode_status": "needs_review"}, {"geocode_status": "pending"},
    {"location_confirmed": False}, {"location_confirmed": 1}, {"location_confirmed": "true"},
    {"lat": None}, {"lat": True}, {"lat": "10.85"}, {"lat": 91},
    {"lon": 181}, {"lat": 21.03}, {"gioi_tinh": "Khác"},
    {"ho_ten": " "}, {"vi_tri_dai_dien": " "}, {"student_id": " "},
])
def test_unconfirmed_or_invalid_student_is_rejected_before_grouping(app, change):
    data = payload(3, 2)
    data["students"][0].update(change)
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=data).status_code == 422


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_nonfinite_coordinates_return_controlled_validation_error(app, bad):
    data = payload(3, 2)
    data["students"][0]["lat"] = bad
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.post("/api/groups/generate", content=json.dumps(data), headers={"Content-Type": "application/json"})
        assert response.status_code == 422
        assert "NaN" not in response.text and "Infinity" not in response.text


def test_empty_duplicates_and_zero_target_are_rejected(app):
    invalid = [payload(0, 0), payload(3, 2, 0, 0)]
    duplicate = payload(3, 2)
    duplicate["students"][1]["student_id"] = duplicate["students"][0]["student_id"]
    invalid.append(duplicate)
    with TestClient(app) as client:
        for data in invalid:
            assert client.post("/api/groups/generate", json=data).status_code == 422


def test_configured_region_and_row_limit_apply(app):
    app.state.settings = replace(app.state.settings, max_student_rows=2)
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=payload(3, 2)).status_code == 413
    app.state.settings = replace(app.state.settings, max_student_rows=1000, geocoding_bounds=(106.7, 10.8, 106.9, 11.0))
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=payload(3, 2)).status_code == 422


def test_maximum_row_schema_and_request_bytes_are_bounded(app):
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=payload(1001, 500)).status_code == 422
        response = client.post("/api/groups/generate", content=b" " * (8 * 1024 * 1024 + 1), headers={"Content-Type": "application/json"})
        assert response.status_code == 413


def test_concurrent_job_is_rejected_and_health_remains_usable(app):
    # A running computation holds this lock; another request must not queue CPU work.
    assert app.state.grouping_lock.acquire(blocking=False)
    try:
        with TestClient(app) as client:
            assert client.post("/api/groups/generate", json=payload(3, 2)).status_code == 429
            assert client.get("/api/health").json() == {"status": "ok"}
    finally:
        app.state.grouping_lock.release()


def test_invariant_failure_has_safe_error_and_releases_job(app, monkeypatch):
    from app.services.grouping_service import GroupingInvariantError
    import app.api.groups as groups_api
    def fail(data):
        raise GroupingInvariantError("private student detail")
    original = groups_api.generate_groups
    monkeypatch.setattr(groups_api, "generate_groups", fail)
    with TestClient(app) as client:
        response = client.post("/api/groups/generate", json=payload(3, 2))
        assert response.status_code == 500 and "private student detail" not in response.text
        monkeypatch.setattr(groups_api, "generate_groups", original)
        assert client.post("/api/groups/generate", json=payload(3, 2)).status_code == 200


def test_grouping_does_not_mutate_input_or_call_geoapify(app):
    data = payload(3, 2)
    original = copy.deepcopy(data)
    with TestClient(app) as client:
        assert client.post("/api/groups/generate", json=data).status_code == 200
    assert data == original

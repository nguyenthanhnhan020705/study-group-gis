"""No server-side student history or cross-request geocoding cache."""
from io import BytesIO
import logging

import httpx
from fastapi.testclient import TestClient

from grouping_fixtures import payload
from phase7_provider import make_app, provider


def test_two_clients_do_not_retrieve_each_others_students_or_history(xlsx, tmp_path, monkeypatch, caplog):
    monkeypatch.chdir(tmp_path)
    app = make_app()
    caplog.set_level(logging.WARNING)
    with TestClient(app) as first, TestClient(app) as second:
        for client, name in [(first, "PRIVATE_FIXTURE_A"), (second, "PRIVATE_FIXTURE_B")]:
            imported = client.post("/api/students/import", files={"file": ("private.xlsx", xlsx([[name, "Nam", "Đường mẫu"]]))})
            assert imported.status_code == 200
            assert [s["ho_ten"] for s in imported.json()["students"]] == [name]
            data = payload(1, 1)
            data["students"][0]["ho_ten"] = name
            result = client.post("/api/groups/generate", json=data)
            assert result.status_code == 200
            assert result.json()["groups"][0]["members"][0]["ho_ten"] == name
            assert client.post("/api/groups/export", json=result.json()).status_code == 200
        for client in (first, second):
            assert client.get("/api/students/import").status_code == 405
            assert client.get("/api/groups/generate").status_code == 405
            for path in ("/api/students", "/api/groups", "/api/history"):
                assert client.get(path).status_code == 404
            assert "PRIVATE_FIXTURE" not in client.get("/api/health").text
            assert "phase7-fixture-secret" not in client.get("/openapi.json").text
        assert list(tmp_path.iterdir()) == []
    assert "PRIVATE_FIXTURE" not in caplog.text
    assert "phase7-fixture-secret" not in caplog.text


def test_provider_cache_is_request_scoped_and_not_a_student_history():
    calls = []
    def handler(request):
        calls.append(request.url.path)
        return provider(request)
    with TestClient(make_app(handler)) as client:
        address = "Cư xá A, KTX Nông Lâm, phường Linh Xuân, TP.HCM"
        reply = client.post("/api/geocode/batch", json={"students": [
            {"student_id": "PRIVATE_A", "address": address}, {"student_id": "PRIVATE_B", "address": address}]}).json()
        assert [s["student_id"] for s in reply["results"]] == ["PRIVATE_A", "PRIVATE_B"]
        assert len(calls) == 1  # Within one batch only.
        reply = client.post("/api/geocode/retry", json={"student_id": "PRIVATE_C", "address": address})
        assert len(calls) == 2  # A different request fetches again.
        assert reply.json()["student_id"] == "PRIVATE_C"
        assert "PRIVATE_A" not in reply.text and "PRIVATE_B" not in reply.text

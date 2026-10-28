from dataclasses import replace

import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app


def client(**limits):
    settings = Settings(cors_origins=("http://127.0.0.1:5500",))
    return TestClient(create_app(replace(settings, **limits)))


def upload(api, data, filename="students.xlsx"):
    return api.post("/api/students/import", files={"file": (filename, data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")})


def test_valid_upload_and_initial_unverified_state(xlsx):
    with client() as api:
        response = upload(api, xlsx([["A", "Nam", "Đường A"], ["B", "Nữ", "Đường B"]]))
    assert response.status_code == 200
    result = response.json()
    assert result["can_proceed"]
    assert result["summary"] == {"total": 2, "male": 1, "female": 1, "invalid_rows": 0}
    assert all(s["geocode_status"] == "pending" and s["lat"] is None for s in result["students"])


def test_bad_row_is_returned_not_silently_dropped(xlsx):
    with client() as api:
        response = upload(api, xlsx([["A", "unknown", "Đường A"]]))
    assert response.status_code == 200
    result = response.json()
    assert not result["can_proceed"] and len(result["students"]) == 1
    assert result["errors"][0]["excel_row"] == 2
    assert result["errors"][0]["field"] == "Giới tính"


@pytest.mark.parametrize("filename", ["students.csv", "students.xls", "students.xlsx.exe"])
def test_non_xlsx_name_is_rejected(xlsx, filename):
    with client() as api:
        response = upload(api, xlsx([["A", "Nam", "A"]]), filename)
    assert response.status_code == 400
    assert response.json()["errors"]


def test_corrupt_file_returns_readable_error():
    with client() as api:
        response = upload(api, b"not an xlsx")
    assert response.status_code == 400
    assert response.json()["errors"][0]["message"]
    assert "Traceback" not in response.text


def test_missing_file_has_common_error_shape():
    with client() as api:
        response = api.post("/api/students/import")
    assert response.status_code == 422
    assert response.json()["errors"][0]["field"] == "file"


def test_configured_upload_and_row_limits(xlsx):
    content = xlsx([["A", "Nam", "A"], ["B", "Nữ", "B"]])
    with client(max_upload_bytes=len(content)-1) as api:
        assert upload(api, content).status_code == 413
    with client(max_upload_bytes=len(content)) as api:
        assert upload(api, content).status_code == 200
    with client(max_student_rows=1) as api:
        response = upload(api, content)
        assert response.status_code == 422
        assert not response.json()["can_proceed"]


def test_oversized_chunked_request_is_bounded():
    with client(max_upload_bytes=100) as api:
        response = api.post("/api/students/import", content=iter([b"a" * 40000, b"b" * 40000]), headers={"Content-Type": "multipart/form-data; boundary=x", "Origin": "http://127.0.0.1:5500"})
    assert response.status_code == 413
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"


def test_post_preflight_is_allowed():
    with client() as api:
        response = api.options("/api/students/import", headers={"Origin": "http://127.0.0.1:5500", "Access-Control-Request-Method": "POST"})
    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"

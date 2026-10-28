"""Exercise the real HTTP grouping API using reproducible synthetic test fixtures.

Starts/stops an isolated local API server; never calls Geoapify or reads its key.
Does not depend on saved browser sessions, Excel files or previous test outputs.
"""
import json
from pathlib import Path
import subprocess
import sys
import time

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / ".local-tests/phase-4"
sys.path.insert(0, str(ROOT / "tests"))
from grouping_fixtures import payload


def check(client, name, rows, expected_sizes, expected_gender=None):
    request = {"students": rows, "target_male": 3, "target_female": 2}
    response = client.post("/api/groups/generate", json=request)
    response.raise_for_status()
    result = response.json()
    assert sorted(group["size"] for group in result["groups"]) == sorted(expected_sizes)
    output_ids = [member["student_id"] for group in result["groups"] for member in group["members"]]
    assert sorted(output_ids) == sorted(row["student_id"] for row in rows)
    assert len(set(output_ids)) == len(rows)
    if expected_gender:
        assert all((group["male"], group["female"]) == expected_gender for group in result["groups"])
    pair_count = sum(group["size"] * (group["size"] - 1) // 2 for group in result["groups"])
    assert result["overall_metrics"]["pair_count"] == pair_count
    (OUTPUT / f"{name}-request.json").write_text(json.dumps(request, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUTPUT / f"{name}-response.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    summary = {"case": name, "students": len(rows), "k": result["k"],
               "groups": [{key: group[key] for key in ("group_id", "size", "male", "female")} for group in result["groups"]],
               "overall_metrics": result["overall_metrics"], "warning_codes": [item["code"] for item in result["warnings"]]}
    print(json.dumps(summary, ensure_ascii=True), flush=True)
    return summary


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    rows = payload(12, 6)["students"]
    with (OUTPUT / "api-server.log").open("w", encoding="utf-8") as log:
        server = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--app-dir", "backend", "--host", "127.0.0.1", "--port", "8014"], cwd=ROOT, stdout=log, stderr=log)
        try:
            with httpx.Client(base_url="http://127.0.0.1:8014", timeout=60, trust_env=False) as client:
                deadline = time.monotonic() + 30
                while True:
                    if server.poll() is not None:
                        raise RuntimeError("Demo API server failed to start; inspect api-server.log")
                    try:
                        if client.get("/api/health").status_code == 200:
                            break
                    except httpx.HTTPError:
                        pass
                    if time.monotonic() >= deadline:
                        raise RuntimeError("Demo API server startup timeout")
                    time.sleep(0.2)
                assert client.get("/openapi.json").json()["info"]["version"] == "0.4.0"
                results = [check(client, "synthetic-12", rows, [6, 6], (3, 3))]
                synthetic = payload()["students"]
                results.append(check(client, "synthetic-30", synthetic, [5] * 6, (3, 2)))
                invalid = payload(12, 6)["students"]
                invalid[0]["location_confirmed"] = False
                assert client.post("/api/groups/generate", json={"students": invalid, "target_male": 3, "target_female": 2}).status_code == 422
                (OUTPUT / "api-summary.json").write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
                print("PASS: real HTTP, reproducible synthetic cases12/30; unconfirmed input rejected; no previous artifacts needed", flush=True)
        finally:
            if server.poll() is None:
                server.terminate()
                server.wait(timeout=10)


if __name__ == "__main__":
    main()

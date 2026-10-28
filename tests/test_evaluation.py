"""Evaluation must reject unverified input and compare identical constraints."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest

from app.schemas.group import GenerateGroupsRequest
from app.services.grouping_service import generate_groups
from grouping_fixtures import payload

SCRIPT = Path(__file__).resolve().parents[1] / "scripts/evaluate_grouping.py"


@pytest.fixture
def evaluation():
    assert SCRIPT.exists(), "Missing reproducible evaluation command"
    spec = importlib.util.spec_from_file_location("evaluate_grouping", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("change", [
    {"location_confirmed": False}, {"geocode_status": "needs_review"},
    {"lat": float("nan")}, {"lon": float("inf")}, {"lat": 21.03},
    {"student_id": "S0001"}, {"unknown": "not allowed"},
])
def test_invalid_snapshot_is_rejected_before_evaluation(evaluation, change):
    data = payload(6, 4)
    data["students"][0].update(change)
    with pytest.raises(ValueError):
        evaluation.evaluate_bytes(json.dumps(data).encode())


@pytest.mark.parametrize("n,male,m,f", [(30, 18, 3, 2), (31, 19, 3, 2), (12, 1, 2, 2), (9, 9, 3, 0)])
def test_all_random_seeds_preserve_members_and_exact_per_group_quotas(evaluation, n, male, m, f):
    request = GenerateGroupsRequest.model_validate(payload(n, male, m, f))
    groups = generate_groups(request).groups
    for seed in range(30):
        partition = evaluation.random_partition(request.students, groups, seed)
        members = [s.student_id for group in partition for s in group]
        assert sorted(members) == sorted(s.student_id for s in request.students)
        assert [(len(g), sum(s.gioi_tinh == "Nam" for s in g)) for g in partition] == [(g.size, g.male) for g in groups]
        again = evaluation.random_partition(request.students, groups, seed)
        assert partition == again


def test_metrics_weight_pairs_and_detect_missing_duplicate_ids(evaluation):
    data = payload(6, 3)
    for row, lat in zip(data["students"], [10.5, 10.51, 10.5, 10.51, 10.52, 10.5]):
        row.update(lat=lat, lon=106.8)
    request = GenerateGroupsRequest.model_validate(data)
    a, b, c, d, e, f = request.students
    metrics = evaluation.partition_metrics([[a, b], [c, d, e], [f]], request)
    # 4 pairs: distances .01 + (.01 + .02 + .01) degrees latitude.
    assert metrics["pair_count"] == 4
    assert metrics["mean_distance_m"] == pytest.approx(1389.938503, abs=.001)
    assert metrics["max_distance_m"] == pytest.approx(2223.901605, abs=.001)
    assert metrics["missing_count"] == metrics["duplicate_count"] == 0
    broken = evaluation.partition_metrics([[a, a], [c, d, e], [f]], request)
    assert broken["missing_count"] == broken["duplicate_count"] == 1
    assert metrics["size_spread"] == 2
    assert metrics["gender_absolute_deviation"] == 9


@pytest.mark.parametrize("data", [payload(3, 2, 1, 0), payload(6, 4, identical=True)])
def test_zero_distance_and_singletons_are_ties_not_improvements(evaluation, data):
    encoded = json.dumps(data).encode()
    report = evaluation.evaluate_bytes(encoded)
    assert report == evaluation.evaluate_bytes(encoded)
    assert report["algorithm"]["mean_distance_m"] == 0
    assert report["baseline"]["mean_distance_m"]["mean"] == 0
    assert report["comparison"]["better_seed_fraction"] == 0
    assert report["comparison"]["tied_seed_fraction"] == 1
    assert report["comparison"]["mean_reduction_percent"] is None
    assert [r["seed"] for r in report["baseline_runs"]] == list(range(30))


def test_cli_hashes_exact_input_and_writes_only_aggregate_report(evaluation, tmp_path):
    import hashlib
    source = tmp_path / "confirmed.json"
    output = tmp_path / "report.json"
    source.write_text(json.dumps(payload(6, 4)), encoding="utf8")
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--input", str(source), "--output", str(output)], capture_output=True)
    assert result.returncode == 0, result.stderr
    report = json.loads(output.read_text(encoding="utf8"))
    assert report["input_sha256"] == hashlib.sha256(source.read_bytes()).hexdigest()
    assert report["n"] == 6
    assert report["algorithm_seed"] == 42
    assert "Sinh viên" not in output.read_text(encoding="utf8")
    assert "student_id" not in output.read_text(encoding="utf8")
    source.write_text('{"students": [{"ho_ten": "PRIVATE NAME"}]}', encoding="utf8")
    output.unlink()
    result = subprocess.run([sys.executable, "-B", str(SCRIPT), "--input", str(source), "--output", str(output)], capture_output=True)
    assert result.returncode != 0 and not output.exists()
    assert b"PRIVATE NAME" not in result.stderr

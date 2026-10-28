import math

import pytest

from grouping_fixtures import payload


def generate(data):
    from app.schemas.group import GenerateGroupsRequest
    from app.services.grouping_service import generate_groups
    return generate_groups(GenerateGroupsRequest.model_validate(data)).model_dump()


@pytest.mark.parametrize("n,male,m,f,want_k", [
    (30, 18, 3, 2, 6), (34, 19, 3, 2, 6), (34, 23, 3, 2, 6),
    (42, 25, 3, 2, 8), (3, 2, 3, 2, 1), (12, 1, 3, 2, 2),
    (12, 11, 3, 2, 2), (20, 0, 3, 2, 4), (20, 20, 3, 2, 4),
    (12, 6, 0, 5, 2), (12, 6, 5, 0, 2), (1, 0, 1, 0, 1),
    (11, 6, 0, 1, 11), (11, 6, 1, 0, 11),
])
def test_group_counts_balanced_sizes_no_lost_or_duplicate_students(n, male, m, f, want_k):
    data = payload(n, male, m, f)
    result = generate(data)
    assert result["k"] == want_k
    assert len(result["groups"]) == want_k
    ids = [member["student_id"] for group in result["groups"] for member in group["members"]]
    assert sorted(ids) == sorted(row["student_id"] for row in data["students"])
    assert len(set(ids)) == n
    sizes = [group["size"] for group in result["groups"]]
    assert min(sizes) >= 1 and max(sizes) - min(sizes) <= 1
    assert len(result["assignments"]) == n
    for group in result["groups"]:
        assert group["male"] == sum(row["gioi_tinh"] == "Nam" for row in group["members"])
        assert group["male"] + group["female"] == group["size"]
        assert group["male_delta"] == group["male"] - m
        assert group["female_delta"] == group["female"] - f
        assert math.isfinite(group["metrics"]["mean_distance_m"])
        assert all({"student_id": member["student_id"], "group_id": group["group_id"]} in result["assignments"] for member in group["members"])


def test_exact_gender_targets_and_geographically_separated_clusters():
    result = generate(payload())
    assert all((group["male"], group["female"]) == (3, 2) for group in result["groups"])
    assert all(group["metrics"]["max_distance_m"] < 400 for group in result["groups"])
    assert result["warnings"] == []
    assert result["strategy"] == "separate_gender_kmeans_hungarian"


@pytest.mark.parametrize("n,male", [(30, 18), (34, 19), (12, 1), (12, 0), (6, 3)])
def test_identical_positions_preserve_k_and_all_members(n, male):
    result = generate(payload(n, male, identical=True))
    assert len(result["groups"]) == max(1, n // 5)
    assert sum(group["size"] for group in result["groups"]) == n
    assert max(group["size"] for group in result["groups"]) - min(group["size"] for group in result["groups"]) <= 1
    assert result["overall_metrics"]["mean_distance_m"] == 0


def test_reproducible_even_when_input_order_changes():
    data = payload(34, 23)
    first = generate(data)
    data["students"].reverse()
    assert generate(data) == first


def test_gender_shortage_warns_without_reducing_k():
    result = generate(payload(30, 1))
    assert result["k"] == 6
    assert any(item["code"] == "minority_fallback" for item in result["warnings"])
    mismatch = next(item for item in result["warnings"] if item["code"] == "target_mismatch")
    assert mismatch["group_ids"] == [1, 2, 3, 4, 5, 6]

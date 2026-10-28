import math

import pytest


def test_haversine_known_distances_symmetry_and_antipodes():
    from app.services.metrics_service import haversine_m
    assert haversine_m((0, 0), (0, 1)) == pytest.approx(111195.0802, abs=0.01)
    assert haversine_m((0, 1), (0, 0)) == pytest.approx(111195.0802, abs=0.01)
    assert haversine_m((0, 0), (0, 180)) == pytest.approx(20015114.442, abs=0.01)
    assert haversine_m((10.85, 106.76), (10.85, 106.76)) == 0


def test_pair_metrics_and_empty_singleton_are_finite():
    from app.services.metrics_service import pair_metrics
    for points in [[], [(10.85, 106.76)], [(10.85, 106.76)] * 3]:
        result = pair_metrics(points)
        assert result["mean_distance_m"] == result["max_distance_m"] == 0
    result = pair_metrics([(0, 0), (0, 1), (0, 2)])
    assert result["pair_count"] == 3
    assert result["mean_distance_m"] == pytest.approx(148260.107, abs=0.01)
    assert result["max_distance_m"] == pytest.approx(222390.160, abs=0.01)


def test_overall_mean_weights_pairs_not_groups():
    from app.services.metrics_service import aggregate_metrics
    result = aggregate_metrics([
        {"pair_count": 1, "mean_distance_m": 100, "max_distance_m": 100},
        {"pair_count": 3, "mean_distance_m": 300, "max_distance_m": 450},
        {"pair_count": 0, "mean_distance_m": 0, "max_distance_m": 0},
    ])
    assert result == {"pair_count": 4, "mean_distance_m": 250, "max_distance_m": 450}
    assert aggregate_metrics([])["mean_distance_m"] == 0


def test_projection_preserves_axis_order_and_uses_metres():
    from app.services.metrics_service import project_points, unproject_points
    points = [(10.85, 106.76), (10.86, 106.76)]
    projected = project_points(points)
    assert 650000 < projected[0][0] < 750000
    assert 1100000 < projected[0][1] < 1300000
    assert math.dist(projected[0], projected[1]) == pytest.approx(1106.4, abs=2)
    restored = unproject_points(projected)
    for actual, expected in zip(restored, points):
        assert tuple(actual) == pytest.approx(expected, abs=1e-8)

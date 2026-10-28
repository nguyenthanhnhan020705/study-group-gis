"""Offline, reproducible comparison on a confirmed GenerateGroupsRequest snapshot.

No geocoding, no invented coordinates, no student identities in the report.
Baseline preserves each algorithm group's size and gender quota exactly.
"""
import argparse
from collections import Counter
import hashlib
import importlib.metadata
import json
from pathlib import Path
import random
import statistics
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.config import Settings
from app.schemas.group import GenerateGroupsRequest
from app.services.grouping_service import generate_groups
from app.services.metrics_service import aggregate_metrics, pair_metrics


def random_partition(students, quotas, seed):
    rng = random.Random(seed)
    pools = {gender: sorted((s for s in students if s.gioi_tinh == gender), key=lambda s: s.student_id)
             for gender in ("Nam", "Nữ")}
    for pool in pools.values():
        rng.shuffle(pool)
    offsets = {gender: 0 for gender in pools}
    groups = []
    for quota in quotas:
        group = []
        for gender, count in (("Nam", quota.male), ("Nữ", quota.female)):
            start = offsets[gender]
            group.extend(pools[gender][start:start + count])
            offsets[gender] += count
        if len(group) != quota.size:
            raise ValueError("Invalid baseline quota")
        groups.append(group)
    if any(offsets[g] != len(pools[g]) for g in pools):
        raise ValueError("Baseline quotas do not conserve students")
    return groups


def partition_metrics(groups, request):
    counts = Counter(s.student_id for group in groups for s in group)
    expected = {s.student_id for s in request.students}
    sizes = [len(group) for group in groups]
    quotas = [(sum(s.gioi_tinh == "Nam" for s in group), sum(s.gioi_tinh == "Nữ" for s in group)) for group in groups]
    return {**aggregate_metrics([pair_metrics([(s.lat, s.lon) for s in group]) for group in groups]),
            "missing_count": len(expected - counts.keys()),
            "duplicate_count": sum(count - 1 for count in counts.values()),
            "unexpected_count": len(counts.keys() - expected),
            "size_spread": max(sizes, default=0) - min(sizes, default=0),
            "gender_absolute_deviation": sum(abs(m - request.target_male) + abs(f - request.target_female) for m, f in quotas)}


def describe(values):
    return {"mean": statistics.mean(values), "std_population": statistics.pstdev(values),
            "median": statistics.median(values), "min": min(values), "max": max(values)}


def evaluate_bytes(content):
    if len(content) > 8 * 1024 * 1024:
        raise ValueError("Snapshot exceeds 8 MiB")
    request = GenerateGroupsRequest.model_validate_json(content)
    west, south, east, north = Settings(cors_origins=()).geocoding_bounds
    if any(not (south <= s.lat <= north and west <= s.lon <= east) for s in request.students):
        raise ValueError("Snapshot outside study bounds")
    result = generate_groups(request)
    algorithm = partition_metrics([g.members for g in result.groups], request)
    runs = []
    for seed in range(30):
        baseline = partition_metrics(random_partition(request.students, result.groups, seed), request)
        if any(baseline[key] for key in ("missing_count", "duplicate_count", "unexpected_count")):
            raise ValueError("Baseline partition invalid")
        runs.append({"seed": seed, **baseline})
    mean = statistics.mean(run["mean_distance_m"] for run in runs)
    tolerance = 1e-9  # Numerical ties in metres, not a practical significance claim.
    better = sum(algorithm["mean_distance_m"] < run["mean_distance_m"] - tolerance for run in runs)
    ties = sum(abs(algorithm["mean_distance_m"] - run["mean_distance_m"]) <= tolerance for run in runs)
    return {"input_sha256": hashlib.sha256(content).hexdigest(), "n": len(request.students), "k": result.k,
            "algorithm_seed": result.seed, "algorithm_strategy": result.strategy,
            "targets": {"male": request.target_male, "female": request.target_female},
            "group_quotas": [{"size": g.size, "male": g.male, "female": g.female} for g in result.groups],
            "environment": {"python": sys.version.split()[0], **{name: importlib.metadata.version(name) for name in ("numpy", "scipy", "scikit-learn", "pyproj")}},
            "algorithm": algorithm, "baseline_runs": runs,
            "baseline": {key: describe([r[key] for r in runs]) for key in algorithm},
            "comparison": {"better_seed_fraction": better / 30, "tied_seed_fraction": ties / 30,
                           "worse_seed_fraction": (30 - better - ties) / 30,
                           "mean_reduction_percent": 100 * (mean - algorithm["mean_distance_m"]) / mean if mean else None},
            "method": "Haversine metres; weighted by all within-group pairs; random Nam/Nu shuffles with fixed quotas; seeds 0..29; population std; 1e-9 metre tie tolerance",
            "limits": "Confirmed flags are input assertions, not independent location verification. One snapshot, 30 random partitions; no population accuracy, travel-time or global-optimality claim."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.input.resolve() == args.output.resolve():
            raise ValueError("Input and output must differ")
        if args.input.stat().st_size > 8 * 1024 * 1024:
            raise ValueError("Snapshot exceeds limit")
        report = evaluate_bytes(args.input.read_bytes())
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n", encoding="utf8")
    except (ValueError, OSError):
        print("Evaluation failed: check confirmed snapshot schema, coordinates and file paths. No student data printed.", file=sys.stderr)
        return 1
    print(f"Evaluated {report['n']} students, {report['k']} groups, 30 fixed baseline seeds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

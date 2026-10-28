"""Separate-gender KMeans, capacity balancing and feasible Hungarian matching."""
import numpy as np
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
from threadpoolctl import threadpool_limits

from app.schemas.group import GenerateGroupsRequest, GenerateGroupsResponse
from app.services.metrics_service import aggregate_metrics, haversine_matrix, pair_metrics, project_points, unproject_points

SEED = 42


class GroupingInvariantError(RuntimeError):
    """An internal assignment failed its conservation or balance checks."""


def _capacities(n, k):
    base, remainder = divmod(n, k)
    return np.array([base + (i < remainder) for i in range(k)], dtype=int)


def _assign_slots(points, centers, capacities):
    slots = np.repeat(np.arange(len(centers)), capacities)
    if len(points) != len(slots):
        raise GroupingInvariantError("Slot count differs from student count")
    clusters = [[] for _ in centers]
    if len(points):
        source, destination = linear_sum_assignment(cdist(points, centers[slots], metric="sqeuclidean"))
        for row, slot in zip(source, destination):
            clusters[int(slots[slot])].append(int(row))
    return clusters


def _balanced_clusters(points, k):
    # Repeated positions may provide fewer distinct KMeans centers than requested.
    # Keep k slots/groups, repeating anchors rather than dropping students or k.
    unique_count = len(np.unique(points, axis=0))
    count = min(k, unique_count)
    if count == 1:
        centers = points.mean(axis=0, keepdims=True)
    else:
        centers = KMeans(n_clusters=count, random_state=SEED, n_init=10, max_iter=300).fit(points).cluster_centers_
    centers = centers[np.lexsort((centers[:, 1], centers[:, 0]))]
    centers = centers[np.arange(k) % len(centers)]
    centers = centers[np.lexsort((centers[:, 1], centers[:, 0]))]
    clusters = _assign_slots(points, centers, _capacities(len(points), k))
    centers = np.array([points[indices].mean(axis=0) for indices in clusters])
    return clusters, centers


def _partition(students, points, k):
    genders = {gender: [i for i, row in enumerate(students) if row.gioi_tinh == gender] for gender in ("Nam", "Nữ")}
    if k == len(students):
        return [[i] for i in range(len(students))], "singleton_groups", []
    if min(map(len, genders.values())) >= k:
        male, male_centers = _balanced_clusters(points[genders["Nam"]], k)
        female, female_centers = _balanced_clusters(points[genders["Nữ"]], k)
        cost = haversine_matrix(unproject_points(male_centers), unproject_points(female_centers))
        sizes = np.array([len(cluster) for cluster in male])[:, None] + np.array([len(cluster) for cluster in female])[None, :]
        low, rem = divmod(len(students), k)
        cost[~np.isin(sizes, [low, low + bool(rem)])] = np.inf
        left, right = linear_sum_assignment(cost)
        clusters = [[genders["Nam"][i] for i in male[a]] + [genders["Nữ"][i] for i in female[b]] for a, b in zip(left, right)]
        return clusters, "separate_gender_kmeans_hungarian", []

    majority_gender = max(genders, key=lambda gender: len(genders[gender]))
    minority_gender = "Nữ" if majority_gender == "Nam" else "Nam"
    majority_indices, minority_indices = genders[majority_gender], genders[minority_gender]
    majority, centers = _balanced_clusters(points[majority_indices], k)
    remaining = _capacities(len(students), k) - np.array([len(cluster) for cluster in majority])
    minority = _assign_slots(points[minority_indices], centers, remaining)
    clusters = [[majority_indices[i] for i in majority[j]] + [minority_indices[i] for i in minority[j]] for j in range(k)]
    warnings = [{"code": "minority_fallback", "message": f"Giới {minority_gender} có ít hơn {k} sinh viên; phân bổ theo vị trí và giữ cân bằng quy mô.", "group_ids": []}]
    return clusters, "majority_kmeans_minority_slots", warnings


def _check_partition(clusters, n, k):
    indices = [i for cluster in clusters for i in cluster]
    sizes = [len(cluster) for cluster in clusters]
    if len(clusters) != k or sorted(indices) != list(range(n)) or not sizes or min(sizes) < 1 or max(sizes) - min(sizes) > 1:
        raise GroupingInvariantError("Invalid group partition")


def generate_groups(payload: GenerateGroupsRequest) -> GenerateGroupsResponse:
    students = sorted(payload.students, key=lambda student: student.student_id)
    n = len(students)
    k = max(1, n // (payload.target_male + payload.target_female))
    points = project_points([(student.lat, student.lon) for student in students])
    with threadpool_limits(limits=1):
        clusters, strategy, warnings = _partition(students, points, k)
    _check_partition(clusters, n, k)
    clusters = sorted((sorted(cluster) for cluster in clusters), key=lambda cluster: students[cluster[0]].student_id)
    groups, assignments = [], []
    for group_id, indices in enumerate(clusters, 1):
        members = [students[i] for i in indices]
        male = sum(student.gioi_tinh == "Nam" for student in members)
        female = len(members) - male
        center = unproject_points([points[indices].mean(axis=0)])[0]
        groups.append({"group_id": group_id, "members": members, "size": len(members), "male": male, "female": female,
                       "male_delta": male - payload.target_male, "female_delta": female - payload.target_female,
                       "centroid": {"lat": float(center[0]), "lon": float(center[1])},
                       "metrics": pair_metrics([(student.lat, student.lon) for student in members])})
        assignments.extend({"student_id": student.student_id, "group_id": group_id} for student in members)
    mismatches = [group["group_id"] for group in groups if group["male_delta"] or group["female_delta"]]
    if mismatches:
        warnings.append({"code": "target_mismatch", "message": "Một số nhóm lệch số Nam/Nữ mong muốn do tổng số lượng và yêu cầu giữ đủ người, cân bằng quy mô.", "group_ids": mismatches})
    return GenerateGroupsResponse(k=k, target_male=payload.target_male, target_female=payload.target_female,
                                  seed=SEED, strategy=strategy, assignments=assignments, groups=groups,
                                  overall_metrics=aggregate_metrics([group["metrics"] for group in groups]), warnings=warnings)

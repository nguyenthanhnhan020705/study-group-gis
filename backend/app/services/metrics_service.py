"""Representative-point distances, in metres; no routing or travel-time claims."""
import numpy as np
from pyproj import Transformer

EARTH_RADIUS_M = 6_371_008.8
TO_UTM = Transformer.from_crs("EPSG:4326", "EPSG:32648", always_xy=True)
TO_WGS84 = Transformer.from_crs("EPSG:32648", "EPSG:4326", always_xy=True)


def project_points(points):
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    x, y = TO_UTM.transform(points[:, 1], points[:, 0])
    return np.column_stack((x, y))


def unproject_points(points):
    points = np.asarray(points, dtype=float).reshape(-1, 2)
    lon, lat = TO_WGS84.transform(points[:, 0], points[:, 1])
    return np.column_stack((lat, lon))


def haversine_matrix(a, b):
    a = np.radians(np.asarray(a, dtype=float).reshape(-1, 2))
    b = np.radians(np.asarray(b, dtype=float).reshape(-1, 2))
    delta = a[:, None, :] - b[None, :, :]
    h = np.sin(delta[:, :, 0] / 2) ** 2 + np.cos(a[:, None, 0]) * np.cos(b[None, :, 0]) * np.sin(delta[:, :, 1] / 2) ** 2
    return 2 * EARTH_RADIUS_M * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def haversine_m(a, b):
    return float(haversine_matrix([a], [b])[0, 0])


def pair_metrics(points):
    if len(points) < 2:
        return {"pair_count": 0, "mean_distance_m": 0.0, "max_distance_m": 0.0}
    distances = haversine_matrix(points, points)[np.triu_indices(len(points), k=1)]
    return {"pair_count": len(distances), "mean_distance_m": float(distances.mean()), "max_distance_m": float(distances.max())}


def aggregate_metrics(metrics):
    pairs = sum(item["pair_count"] for item in metrics)
    total = sum(item["pair_count"] * item["mean_distance_m"] for item in metrics)
    return {"pair_count": pairs, "mean_distance_m": total / pairs if pairs else 0.0,
            "max_distance_m": max((item["max_distance_m"] for item in metrics), default=0.0)}

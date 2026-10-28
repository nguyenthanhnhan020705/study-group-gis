"""Synthetic confirmed coordinates for algorithm tests, never geocoding evidence."""
import random


def payload(n=30, male=18, target_male=3, target_female=2, identical=False):
    rng = random.Random(2026)
    rows = []
    for i in range(n):
        gender_index = i if i < male else i - male
        cluster = gender_index % 6
        lat = 10.75 + (cluster // 3) * 0.12 + rng.uniform(-0.001, 0.001)
        lon = 106.65 + (cluster % 3) * 0.10 + rng.uniform(-0.001, 0.001)
        rows.append({"student_id": f"S{i:04d}", "ho_ten": f"Sinh viên tổng hợp {i}",
                     "gioi_tinh": "Nam" if i < male else "Nữ", "dia_chi_goc": "Đường tổng hợp",
                     "vi_tri_dai_dien": "Điểm tổng hợp", "lat": 10.85 if identical else lat,
                     "lon": 106.76 if identical else lon, "geocode_status": "verified", "location_confirmed": True})
    return {"students": rows, "target_male": target_male, "target_female": target_female}

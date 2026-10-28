"""Live Geoapify check using public sample addresses; never prints key or raw errors."""
import asyncio
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.core.config import load_settings
from app.schemas.geocoding import GeocodeInput
from app.services.geocoding_service import GeocodeProblem, GeocodingService

ADDRESSES = [
    "Đường Hoàng Diệu 2, TP. Thủ Đức, TP. Hồ Chí Minh",
    "Đường Hoàng Diệu 2, Thành phố Hồ Chí Minh",
    "Ký túc xá khu A, Đại học Quốc gia TP. Hồ Chí Minh",
    "Đường Nguyễn An Ninh, Dĩ An, Bình Dương",
]


async def main():
    service = GeocodingService(load_settings())
    try:
        results = await service.batch([GeocodeInput(student_id=f"PUBLIC-{i+1}", address=address) for i, address in enumerate(ADDRESSES)])
    except GeocodeProblem:
        print("Live check unavailable: verify local key/configuration. No secrets printed.")
        return 1
    output = ROOT / ".local-tests/phase-3/live-geocoding.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps([r.model_dump() for r in results], ensure_ascii=False, indent=2), encoding="utf-8")
    for result in results:
        print(result.student_id, result.status, "candidates", len(result.candidates), "eligible", sum(c.eligible for c in result.candidates), "error", result.error_code)
    return int(any(result.status == "error" for result in results))


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))

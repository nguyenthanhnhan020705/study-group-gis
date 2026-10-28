"""Geoapify boundary: sanitized results, no persistent student/address cache."""

import asyncio
import math
import time

import httpx

from app.schemas.geocoding import Candidate, GeocodeInput, GeocodeResult
from app.services.known_places import resolve_place, normalize
from app.services.address_labels import current_street_label, registered_street

URL = "https://api.geoapify.com/v1/geocode/search"


class GeocodeProblem(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


def finite_number(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value):
        return None
    return float(value)


class GeocodingService:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self.busy = False
        self.next_request = 0.0
        self.cooldown_until = 0.0

    def candidate(self, raw, address=""):
        lat, lon = finite_number(raw.get("lat")), finite_number(raw.get("lon"))
        rank = raw.get("rank") or {}
        confidence = finite_number(rank.get("confidence")) if isinstance(rank, dict) else None
        if confidence is not None and not 0 <= confidence <= 1:
            confidence = None
        kind = str(raw.get("result_type") or "unknown")[:80]
        formatted = str(raw.get("formatted") or "Không có địa chỉ khớp")[:2000]
        west, south, east, north = self.settings.geocoding_bounds
        reason = ""
        if lat is None or lon is None or not (-90 <= lat <= 90 and -180 <= lon <= 180):
            lat, lon = None, None
            reason = "Tọa độ không hợp lệ."
        elif raw.get("country_code", "").lower() != "vn" or not (south <= lat <= north and west <= lon <= east):
            reason = "Kết quả nằm ngoài vùng nghiên cứu hoặc ngoài Việt Nam."
        elif kind not in {"street", "amenity", "suburb", "quarter", "neighbourhood"}:
            reason = "Chưa đạt độ chi tiết đường/khu vực/địa điểm công cộng cho phép."
        elif confidence is None or confidence < self.settings.geocoding_min_confidence:
            reason = "Mức tin cậy thiếu hoặc thấp; hãy bổ sung địa chỉ và kiểm tra lại."
        label = current_street_label(address, raw) if not reason else None
        if not reason and registered_street(address) and label is None:
            reason = "Chưa đối chiếu được đúng đường/phường sau sáp nhập. Hãy kiểm tra lại."
        requested = normalize(address)
        dormitory = any(term in requested for term in ("ky tuc xa", "ktx", "cu xa"))
        name = normalize(str(raw.get("street") if kind == "street" else raw.get("name") or ""))
        context = set(normalize(" ".join(str(raw.get(field) or "") for field in
                      ("formatted", "street", "name", "suburb", "quarter", "neighbourhood", "city", "state"))).split())
        automatic = (not reason and not dormitory and (label is not None or
                     (confidence is not None and confidence >= 0.95 and bool(name)
                      and name in requested and len(name.split()) >= 2 and set(requested.split()) <= context)))
        return Candidate(lat=lat, lon=lon, formatted=label[0] if label else formatted,
                         auto_selectable=bool(automatic),
                         provider_formatted=formatted if label else None,
                         address_source_url=label[1] if label else None,
                         result_type=kind, confidence=confidence, eligible=not reason, reason=reason)

    async def batch(self, rows: list[GeocodeInput]) -> list[GeocodeResult]:
        if not self.settings.geoapify_api_key or self.settings.geoapify_api_key == "replace_with_your_own_key":
            raise GeocodeProblem("Backend chưa cấu hình khóa Geoapify. Vui lòng thiết lập backend/.env.")
        if self.busy or time.monotonic() < self.cooldown_until:
            raise GeocodeProblem("Dịch vụ đang bận hoặc tạm giới hạn truy cập. Vui lòng thử lại sau.", 429)
        self.busy = True
        try:
            results, cache = [], {}
            async with httpx.AsyncClient(timeout=self.settings.geocoding_timeout, transport=self.transport, follow_redirects=False) as client:
                for row in rows:
                    key = " ".join(row.address.split())
                    if key not in cache:
                        if time.monotonic() < self.cooldown_until:
                            cache[key] = GeocodeResult(student_id=row.student_id, address=row.address, status="error", error_code="rate_limit", message="Geoapify giới hạn truy cập. Hãy thử lại sau.")
                        else:
                            await asyncio.sleep(max(0, self.next_request - time.monotonic()))
                            self.next_request = time.monotonic() + self.settings.geocoding_interval
                            cache[key] = await self.lookup(client, row)
                    results.append(cache[key].model_copy(update={"student_id": row.student_id, "address": row.address}, deep=True))
            return results
        finally:
            self.busy = False

    async def lookup(self, client, row):
        result = GeocodeResult(student_id=row.student_id, address=row.address)
        try:
            place = resolve_place(row.address)
            url = "https://api.geoapify.com/v2/places" if place else URL
            params = place.params() if place else {"text": row.address, "filter": "countrycode:vn", "format": "json", "limit": 5}
            response = await client.get(url, params={**params, "apiKey": self.settings.geoapify_api_key})
            if response.status_code in (401, 403):
                return result.model_copy(update={"status": "error", "error_code": "credentials", "message": "Geoapify từ chối khóa hoặc quyền truy cập. Kiểm tra cấu hình backend."})
            if response.status_code == 429:
                self.cooldown_until = time.monotonic() + 30
                return result.model_copy(update={"status": "error", "error_code": "rate_limit", "message": "Geoapify hết quota hoặc giới hạn truy cập. Hãy thử lại sau."})
            response.raise_for_status()
            payload = response.json()
            if place:
                result.candidates = place.candidates(payload, self.settings.geocoding_bounds)
                result.message = ("Vị trí từ Geoapify Places/OSM; địa chỉ hiển thị theo đơn vị quản lý sau sáp nhập. Chọn tòa/điểm đại diện, xem bản đồ rồi xác nhận."
                                  if result.candidates else "Chưa đối chiếu được đúng ký túc xá từ nguồn bản đồ. Không xác nhận các địa điểm trùng tên; hãy kiểm tra lại.")
                return result
            raw_results = payload.get("results")
            if not isinstance(raw_results, list) or any(not isinstance(raw, dict) for raw in raw_results):
                raise ValueError("Invalid response structure")
            result.candidates = [self.candidate(raw, row.address) for raw in raw_results[:5]]
            result.message = "Hãy chọn ứng viên, xem bản đồ rồi xác nhận vị trí đại diện." if result.candidates else "Không tìm thấy địa chỉ. Hãy bổ sung tên đường/khu vực và thử lại."
            return result
        except httpx.TimeoutException:
            code, message = "timeout", "Geoapify phản hồi quá chậm. Vui lòng thử lại."
        except (httpx.HTTPError, ValueError, TypeError, AttributeError):
            code, message = "provider_error", "Không đọc được kết quả Geoapify. Vui lòng thử lại sau."
        return result.model_copy(update={"status": "error", "error_code": code, "message": message})

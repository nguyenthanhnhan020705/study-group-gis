"""Narrow, sourced place identities; coordinates are fetched live, never invented."""
from dataclasses import dataclass, replace
import math
import re
import unicodedata

from app.schemas.geocoding import Candidate

NLU_ADDRESS = "Ký túc xá Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, khu phố 33, phường Linh Xuân, Thành phố Hồ Chí Minh"
VNU_B_ADDRESS = "Ký túc xá khu B Đại học Quốc gia Thành phố Hồ Chí Minh, đường Mạc Đĩnh Chi, khu phố Tân Hòa, phường Đông Hòa, Thành phố Hồ Chí Minh"
CO_MAY_ADDRESS = "Ký túc xá Cỏ May, trong khuôn viên Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, khu phố 33, phường Linh Xuân, Thành phố Hồ Chí Minh"


def normalize(value):
    value = unicodedata.normalize("NFKD", value.lower().replace("đ", "d"))
    value = "".join(char for char in value if not unicodedata.combining(char))
    return " ".join(re.findall(r"[a-z0-9]+", value))


@dataclass(frozen=True)
class KnownPlace:
    address: str
    aliases: tuple[str, ...]
    bounds: tuple[float, float, float, float]
    category: str
    required_category: str
    osm_type: str
    identities: tuple[tuple[int, str], ...]
    address_source_url: str
    gender_policy: tuple[tuple[int, tuple[str, ...]], ...] = ()

    def params(self):
        return {"categories": self.category, "filter": "rect:" + ",".join(map(str, self.bounds)), "limit": 100, "lang": "vi"}

    def candidates(self, payload, project_bounds):
        features = payload.get("features")
        if not isinstance(features, list):
            raise ValueError("Invalid places response")
        approved, found = dict(self.identities), {}
        for feature in features:
            if not isinstance(feature, dict) or not isinstance(feature.get("properties"), dict):
                raise ValueError("Invalid place feature")
            raw = feature["properties"]
            datasource = raw.get("datasource") or {}
            origin = datasource.get("raw") or {}
            osm_id = origin.get("osm_id")
            if osm_id not in approved or origin.get("osm_type") != self.osm_type or datasource.get("sourcename") != "openstreetmap":
                continue
            if normalize(str(raw.get("name", ""))) != normalize(approved[osm_id]) or self.required_category not in (raw.get("categories") or []):
                continue
            lat, lon = raw.get("lat"), raw.get("lon")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (lat, lon)):
                continue
            if raw.get("country_code") != "vn" or any(not (west <= lon <= east and south <= lat <= north) for west, south, east, north in (self.bounds, project_bounds)):
                continue
            label = f"{self.address} — {approved[osm_id]}" if self.osm_type == "w" else self.address
            kind = "way" if self.osm_type == "w" else "node"
            found[osm_id] = Candidate(lat=lat, lon=lon, formatted=label, result_type="amenity", confidence=None,
                                      auto_selectable=len(self.identities) == 1,
                                      eligible=True, reason="", source="geoapify_places",
                                      source_url=f"https://www.openstreetmap.org/{kind}/{osm_id}",
                                      address_source_url=self.address_source_url,
                                      allowed_genders=list(dict(self.gender_policy)[osm_id]) if osm_id in dict(self.gender_policy) else None)
        return [found[osm_id] for osm_id, _ in self.identities if osm_id in found]


PLACES = (
    KnownPlace(
        NLU_ADDRESS,
        (NLU_ADDRESS, "Ký túc xá Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, phường Linh Xuân, Thành phố Hồ Chí Minh",
         "KTX Nông Lâm, phường Linh Xuân, TP.HCM"),
        (106.785, 10.866, 106.795, 10.875), "building", "building.dormitory", "w",
        ((291412044, "Cư xá A"), (291412047, "Cư xá B"), (291412048, "Cư xá C"), (726200672, "Cư xá D"), (609150037, "Cư xá E")),
        "https://ts.hcmuaf.edu.vn/data/file/Tuyen%20sinh%202025/20250718_%20Th%C3%B4ng%20tin%20tuy%E1%BB%83n%20sinh%202025.pdf",
        # Housing rules supplied by the project owner on 2026-10-23; not inferred from OSM.
        ((291412044, ("Nam",)), (291412047, ("Nữ",)), (291412048, ("Nam",)), (726200672, ("Nữ",)), (609150037, ("Nam", "Nữ"))),
    ),
    KnownPlace(
        VNU_B_ADDRESS,
        (VNU_B_ADDRESS, "KTX khu B ĐHQG-HCM, đường Mạc Đĩnh Chi, phường Đông Hòa, TP.HCM"),
        (106.779, 10.879, 106.788, 10.890), "accommodation.guest_house", "accommodation.guest_house", "n",
        ((11562800202, "Ký túc xá Khu B ĐHQG Thành phố Hồ Chí Minh"),),
        "https://www.ktxhcm.edu.vn/",
    ),
    KnownPlace(
        CO_MAY_ADDRESS,
        (CO_MAY_ADDRESS, "KTX Cỏ May, phường Linh Xuân, TP.HCM"),
        (106.785, 10.866, 106.795, 10.875), "building", "building.dormitory", "w",
        ((609150034, "KTX Cỏ May"),), "https://ktxcomay.com.vn/",
        ((609150034, ("Nam", "Nữ")),),
    ),
)


def resolve_place(address):
    normalized = normalize(address)
    exact = next((place for place in PLACES if any(normalized == normalize(alias) for alias in place.aliases)), None)
    if exact:
        return exact
    # Refine an already recognized campus; a bare A/B name remains ambiguous.
    buildings = re.findall(r"\bcu xa ([a-e])\b", normalized)
    campus = " ".join(re.sub(r"\bcu xa [a-e]\b", "", normalized).split())
    if len(set(buildings)) == 1 and any(campus == normalize(alias) for alias in PLACES[0].aliases):
        identities = tuple(item for item in PLACES[0].identities if normalize(item[1]) == f"cu xa {buildings[0]}")
        return replace(PLACES[0], identities=identities)
    return None

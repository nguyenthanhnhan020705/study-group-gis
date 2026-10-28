"""Small sourced display-label registry; never a general merger/coordinate fix."""
from app.services.known_places import normalize

WARD = "phường Thủ Đức"
CITY = "Thành phố Hồ Chí Minh"
STREETS = {
    f"Đường Võ Văn Ngân, {WARD}, {CITY}": (
        {"duong vo van ngan", "vo van ngan street", "vo van ngan"},
        (106.76, 10.84, 106.78, 10.86),
        "https://chicuccntyhcm.gov.vn/new/2025/12/04/Tram-Chan-nuoi-va-Thu-y-khu-vuc-1.aspx",
    ),
    f"Đường Kha Vạn Cân, {WARD}, {CITY}": (
        {"duong kha van can", "kha van can street", "kha van can"},
        (106.75, 10.85, 106.765, 10.865),
        "https://gdnn.tphcm.gov.vn/truong-cao-dang-cong-nghe-tp-ho-chi-minh",
    ),
}


def registered_street(address):
    return next((key for key in STREETS if normalize(key) == normalize(address)), None)


def current_street_label(address, raw):
    key = registered_street(address)
    if key is None:
        return None
    names, (west, south, east, north), source = STREETS[key]
    lat, lon = raw.get("lat"), raw.get("lon")
    if (raw.get("country_code", "").lower() != "vn"
            or raw.get("iso3166_2") != "VN-SG"
            or raw.get("result_type") != "street"
            or normalize(str(raw.get("suburb", ""))) != normalize(WARD)
            or normalize(str(raw.get("street", ""))) not in names
            or isinstance(lat, bool) or isinstance(lon, bool)
            or not isinstance(lat, (int, float)) or not isinstance(lon, (int, float))
            or not (south <= lat <= north and west <= lon <= east)):
        return None
    return key, source

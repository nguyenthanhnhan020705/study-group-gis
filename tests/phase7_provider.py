"""Offline Geoapify boundary fixtures, NOT evidence of geocoding accuracy.

Coordinates are synthetic points inside the registered bounds. OSM identifiers
mirror the existing registry; real-provider validation is a separate command.
Run via uvicorn phase7_provider:app --app-dir tests for browser integration.
"""
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from app.core.config import Settings
from app.main import create_app
from app.services.geocoding_service import GeocodingService

BUILDINGS = [
    (291412044, "Cư xá A", 10.870, 106.790),
    (291412047, "Cư xá B", 10.871, 106.791),
    (291412048, "Cư xá C", 10.872, 106.792),
    (726200672, "Cư xá D", 10.873, 106.793),
    (609150037, "Cư xá E", 10.874, 106.794),
    (609150034, "KTX Cỏ May", 10.8705, 106.7905),
    (11562800202, "Ký túc xá Khu B ĐHQG Thành phố Hồ Chí Minh", 10.883, 106.783),
]


def provider(request):
    if request.url.path == "/v2/places":
        features = []
        for osm_id, name, lat, lon in BUILDINGS:
            node = osm_id == 11562800202
            features.append({"type": "Feature", "geometry": {"type": "Point", "coordinates": [lon, lat]},
                "properties": {"name": name, "lat": lat, "lon": lon, "country_code": "vn",
                    "categories": ["accommodation.guest_house" if node else "building.dormitory"],
                    "datasource": {"sourcename": "openstreetmap", "raw": {"osm_id": osm_id, "osm_type": "n" if node else "w"}}}})
        return httpx.Response(200, json={"features": features})
    assert request.url.path == "/v1/geocode/search"
    address = request.url.params["text"]
    if "Võ Văn Ngân" in address:
        street, lat, lon = "Vo Van Ngan Street", 10.8496978, 106.7691507
    elif "Kha Vạn Cân" in address:
        street, lat, lon = "Đường Kha Vạn Cân", 10.856262, 106.7564858
    else:
        return httpx.Response(200, json={"results": []})
    return httpx.Response(200, json={"results": [{"street": street, "lat": lat, "lon": lon,
        "country_code": "vn", "result_type": "street", "rank": {"confidence": .81},
        "iso3166_2": "VN-SG", "suburb": "Phường Thủ Đức", "formatted": street + ", Phường Thủ Đức"}]})


def make_app(handler=provider):
    settings = Settings(cors_origins=("http://127.0.0.1:5527",), geoapify_api_key="phase7-fixture-secret", geocoding_interval=0)
    application = create_app(settings)
    application.state.geocoding = GeocodingService(settings, transport=httpx.MockTransport(handler))
    return application


app = make_app()

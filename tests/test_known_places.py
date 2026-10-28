import asyncio
from dataclasses import replace

import httpx
import pytest

from app.core.config import Settings
from app.schemas.geocoding import GeocodeInput
from app.services.geocoding_service import GeocodingService

NLU = "Ký túc xá Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, khu phố 33, phường Linh Xuân, Thành phố Hồ Chí Minh"
VNU = "Ký túc xá khu B Đại học Quốc gia Thành phố Hồ Chí Minh, đường Mạc Đĩnh Chi, khu phố Tân Hòa, phường Đông Hòa, Thành phố Hồ Chí Minh"


def feature(nlu=True, **changes):
    properties = {"name": "Cư xá A" if nlu else "Ký túc xá Khu B ĐHQG Thành phố Hồ Chí Minh",
                  "lat": 10.871312 if nlu else 10.8821432, "lon": 106.7911041 if nlu else 106.7825645,
                  "country_code": "vn", "categories": ["building.dormitory"] if nlu else ["accommodation.guest_house"],
                  "formatted": "Old city/district label must not be presented as current address",
                  "datasource": {"sourcename": "openstreetmap", "raw": {"osm_id": 291412044 if nlu else 11562800202, "osm_type": "w" if nlu else "n"}}}
    properties.update(changes)
    return {"type": "Feature", "properties": properties, "geometry": {"type": "Point", "coordinates": [properties["lon"], properties["lat"]]}}


def lookup(address, features, handler=None, **config):
    def respond(request):
        assert request.url.path == "/v2/places"
        assert "rect:" in request.url.params["filter"]
        return httpx.Response(200, json={"features": features})
    settings = replace(Settings(cors_origins=(), geoapify_api_key="test-key"), geocoding_interval=0, **config)
    service = GeocodingService(settings, transport=httpx.MockTransport(handler or respond))
    return asyncio.run(service.batch([GeocodeInput(student_id="S1", address=address)]))[0]


@pytest.mark.parametrize("address,nlu,ward", [(NLU, True, "Linh Xuân"), (VNU, False, "Đông Hòa")])
def test_known_dormitory_uses_real_place_identity_and_new_address_without_fabricating_confidence(address, nlu, ward):
    result = lookup(address, [feature(nlu)])
    assert result.status == "needs_review"
    candidate = result.candidates[0]
    assert candidate.eligible and candidate.confidence is None
    assert candidate.source == "geoapify_places"
    assert ward in candidate.formatted and "Thành phố Hồ Chí Minh" in candidate.formatted
    assert "Old city" not in candidate.formatted and "Dĩ An" not in candidate.formatted
    assert candidate.source_url.startswith("https://www.openstreetmap.org/")


@pytest.mark.parametrize("address", ["  KTX Nông Lâm, phường Linh Xuân, TP.HCM  ", NLU.upper(), NLU.replace(" ", "  ")])
def test_explicit_aliases_allow_case_and_spacing(address):
    assert lookup(address, [feature()]).candidates[0].eligible


@pytest.mark.parametrize("changes", [
    {"name": "KTX Cỏ May"}, {"name": "Cư xá B"},
    {"datasource": {"sourcename": "openstreetmap", "raw": {"osm_id": 999, "osm_type": "w"}}},
    {"datasource": {"sourcename": "unknown", "raw": {"osm_id": 291412044, "osm_type": "w"}}},
    {"lat": 10.80}, {"lat": None}, {"lat": True}, {"lon": float("inf")},
    {"country_code": "us"}, {"categories": ["education.university"]},
])
def test_wrong_identity_or_invalid_coordinate_never_offers_confirmable_place(changes):
    result = lookup(NLU, [feature(**changes)])
    assert not any(candidate.eligible for candidate in result.candidates)


def test_project_region_still_applies_to_known_place():
    result = lookup(NLU, [feature()], geocoding_bounds=(106.4, 10.5, 106.7, 10.8))
    assert not any(candidate.eligible for candidate in result.candidates)


@pytest.mark.parametrize("address", ["KTX khu A Đại học Quốc gia TP.HCM", "KTX Cỏ May, Linh Xuân, TP.HCM", "KTX Nông Lâm, Thái Nguyên", "KTX khu B"])
def test_other_or_ambiguous_dormitory_does_not_match_curated_identity(address):
    def handler(request):
        assert request.url.path == "/v1/geocode/search"
        return httpx.Response(200, json={"results": []})
    assert lookup(address, [], handler).candidates == []


def test_places_credentials_error_is_safe():
    result = lookup(VNU, [], lambda request: httpx.Response(403, text="test-key private detail"))
    assert result.error_code == "credentials"
    assert "test-key" not in result.model_dump_json() and "private detail" not in result.model_dump_json()


@pytest.mark.parametrize("osm_id,name,expected", [
    (291412044, "Cư xá A", ["Nam"]), (291412047, "Cư xá B", ["Nữ"]),
    (291412048, "Cư xá C", ["Nam"]), (726200672, "Cư xá D", ["Nữ"]),
    (609150037, "Cư xá E", ["Nam", "Nữ"]),
])
def test_nlu_gender_policy_provided_by_user(osm_id, name, expected):
    item = feature(name=name, datasource={"sourcename": "openstreetmap", "raw": {"osm_id": osm_id, "osm_type": "w"}})
    candidate = lookup(NLU, [item]).candidates[0]
    assert candidate.allowed_genders == expected


def test_co_may_remains_separate_place_and_allows_both_genders():
    address = "Ký túc xá Cỏ May, trong khuôn viên Trường Đại học Nông Lâm Thành phố Hồ Chí Minh, khu phố 33, phường Linh Xuân, Thành phố Hồ Chí Minh"
    item = feature(name="KTX Cỏ May", datasource={"sourcename": "openstreetmap", "raw": {"osm_id": 609150034, "osm_type": "w"}})
    result = lookup(address, [item])
    assert len(result.candidates) == 1
    assert "Cỏ May" in result.candidates[0].formatted
    assert result.candidates[0].allowed_genders == ["Nam", "Nữ"]
    assert result.candidates[0].confidence is None

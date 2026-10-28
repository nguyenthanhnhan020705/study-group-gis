"""Only independently checked street/ward matches may get a current label."""
import httpx
import pytest

from test_geocoding import run_lookup, candidate

ADDRESS = "Đường Võ Văn Ngân, phường Thủ Đức, Thành phố Hồ Chí Minh"


def lookup(**changes):
    raw = candidate(lat=10.8496978, lon=106.7691507,
                    street="Vo Van Ngan Street", suburb="Phường Thủ Đức",
                    iso3166_2="VN-SG", formatted="Vo Van Ngan Street, Thủ Đức, Vietnam")
    raw.update(changes)
    return run_lookup(lambda _: httpx.Response(200, json={"results": [raw]}),
                      [{"student_id": "S1", "address": ADDRESS}])[0].candidates[0]


def test_current_label_preserves_provider_evidence_and_coordinates():
    result = lookup()
    assert result.formatted == ADDRESS
    assert result.provider_formatted == "Vo Van Ngan Street, Thủ Đức, Vietnam"
    assert result.address_source_url.startswith("https://")
    assert (result.lat, result.lon, result.confidence) == (10.8496978, 106.7691507, .95)


def test_registered_street_can_auto_match_after_independent_name_ward_and_region_checks():
    result = lookup(rank={"confidence": .81})
    assert result.auto_selectable and result.confidence == .81
    assert not lookup(suburb="Phường Hiệp Bình", rank={"confidence": .99}).auto_selectable


@pytest.mark.parametrize("changes", [
    {"suburb": "Phường Hiệp Bình"}, {"street": "Đường khác"},
    {"lat": 10.99}, {"iso3166_2": "VN-DN"},
    {"rank": {"confidence": .1}}, {"result_type": "amenity"},
])
def test_unmatched_or_unreliable_result_is_never_relabelled(changes):
    result = lookup(**changes)
    assert result.formatted != ADDRESS
    assert result.address_source_url is None


def test_kha_van_can_does_not_accept_same_street_in_another_ward():
    from app.services.address_labels import current_street_label
    raw = {"street": "Đường Kha Vạn Cân", "suburb": "Phường Hiệp Bình",
           "iso3166_2": "VN-SG", "lat": 10.8264381, "lon": 106.712283,
           "country_code": "vn", "result_type": "street"}
    address = "Đường Kha Vạn Cân, phường Thủ Đức, Thành phố Hồ Chí Minh"
    assert current_street_label(address, raw) is None
    raw.update(suburb="Phường Thủ Đức", lat=10.856262, lon=106.7564858)
    assert current_street_label(address, raw)[0] == address
    assert current_street_label("Địa chỉ chưa đối chiếu", raw) is None

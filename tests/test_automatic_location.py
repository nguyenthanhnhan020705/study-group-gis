from io import BytesIO

import httpx
import pytest
from openpyxl import Workbook

from app.services.excel_service import parse_students
from test_known_places import lookup, feature, NLU, VNU
from test_geocoding import run_lookup, candidate


def workbook(hint="Cư xá A", title="Cư xá/Khu vực"):
    book = Workbook()
    book.active.append(["Họ và tên", "Giới tính", "Nơi ở để học tập", title])
    book.active.append(["Sinh viên thử", "Nam", NLU, hint])
    content = BytesIO(); book.save(content); book.close()
    return content.getvalue()


@pytest.mark.parametrize("title", ["Cư xá/Khu vực", "Điểm cần xác nhận"])
def test_optional_place_column_preserves_original_and_supplies_lookup_address(title):
    result = parse_students(workbook(title=title))
    assert result.can_proceed
    assert result.students[0].dia_chi_goc == NLU
    assert result.students[0].dia_chi_da_sua == f"Cư xá A, {NLU}"


def test_report_sample_uses_all_nine_declared_places_without_duplicate_dormitory_prefix():
    from pathlib import Path
    from app.services.known_places import resolve_place
    rows = parse_students((Path(__file__).resolve().parents[1] / "data/samples/danh_sach_sinh_vien_bao_cao.xlsx").read_bytes())
    assert rows.can_proceed and len(rows.students) == 30
    addresses = {row.dia_chi_da_sua or row.dia_chi_goc for row in rows.students}
    assert len(addresses) == 9
    assert len([address for address in addresses if resolve_place(address)]) == 7


@pytest.mark.parametrize("hint", ["=1+1", "x" * 2001, 123])
def test_invalid_optional_hint_is_reported(hint):
    result = parse_students(workbook(hint))
    assert not result.can_proceed and result.summary.total == 1


def test_explicit_building_only_offers_the_requested_identity_for_auto():
    other = feature(name="Cư xá C", datasource={"sourcename": "openstreetmap", "raw": {"osm_id":291412048,"osm_type":"w"}})
    result = lookup(f"Cư xá A, {NLU}", [feature(), other])
    assert len(result.candidates) == 1
    assert result.candidates[0].auto_selectable
    assert "Cư xá A" in result.candidates[0].formatted


def test_general_campus_never_guesses_a_building_even_if_only_one_found():
    assert not lookup(NLU, [feature()]).candidates[0].auto_selectable


def test_unique_registered_campus_can_auto_match_without_fabricated_confidence():
    row = lookup(VNU, [feature(False)]).candidates[0]
    assert row.auto_selectable and row.confidence is None


def test_conflicting_building_names_do_not_auto_match():
    result = lookup(f"Cư xá A, Cư xá C, {NLU}", [], lambda request: httpx.Response(200, json={"results": [candidate()]}))
    assert not any(row.auto_selectable for row in result.candidates)


@pytest.mark.parametrize("address,raw,expected", [
    ("Đường kiểm thử", candidate(street="Đường kiểm thử"), True),
    ("Đường kiểm thử", candidate(street="Đường khác"), False),
    ("Đường kiểm thử, Linh Xuân", candidate(street="Đường kiểm thử"), False),
    ("Đường kiểm thử", candidate(street="Đường kiểm thử", rank={"confidence":0.8}), False),
    ("KTX không rõ", candidate(formatted="KTX không rõ", result_type="amenity", name="KTX không rõ"), False),
])
def test_auto_geocoding_requires_name_context_and_high_confidence(address, raw, expected):
    result = run_lookup(lambda request: httpx.Response(200,json={"results":[raw]}), [{"student_id":"S1","address":address}])[0]
    assert result.candidates[0].auto_selectable is expected

import pytest


def parse(content, **kwargs):
    from app.services.excel_service import parse_students
    return parse_students(content, **kwargs)


def test_reordered_headers_extra_columns_and_normalization(xlsx):
    result = parse(xlsx(
        [["ignored", "  Đường A  ", " Nam ", " Nguyễn   Văn A "]],
        ["Dấu thời gian", "Nơi ở để học tập", "Giới tính", "Họ và tên"],
    ))
    assert result.can_proceed
    student = result.students[0]
    assert (student.ho_ten, student.gioi_tinh, student.dia_chi_goc) == ("Nguyễn Văn A", "Nam", "Đường A")
    assert student.excel_row == 2
    assert student.lat is None and student.lon is None
    assert student.geocode_status == "pending" and not student.location_confirmed


def test_duplicates_are_independent_and_ids_repeat_for_same_rows(xlsx):
    content = xlsx([["A", "Nữ", "Đường A"], ["A", "Nữ", "Đường A"]])
    result = parse(content)
    assert len({student.student_id for student in result.students}) == 2
    assert [s.student_id for s in result.students] == [s.student_id for s in parse(content).students]
    assert result.summary.female == 2


def test_invalid_rows_are_retained_with_excel_line_numbers(xlsx):
    result = parse(xlsx([["A", "Nam", "Đường A"], [None, None, None], ["B", "nam", " "], ["C", "Nữ", "Đường C"]]))
    assert not result.can_proceed
    assert len(result.students) == 4
    assert [s.excel_row for s in result.students] == [2, 3, 4, 5]
    assert {(e.excel_row, e.field) for e in result.errors} == {
        (3, "Họ và tên"), (3, "Giới tính"), (3, "Nơi ở để học tập"), (4, "Giới tính"), (4, "Nơi ở để học tập"),
    }
    assert result.summary.model_dump() == {"total": 4, "male": 1, "female": 1, "invalid_rows": 2}
    assert result.students[2].gioi_tinh == "nam"


@pytest.mark.parametrize("headers", [["Họ và tên", "Giới tính"], ["Họ và tên", "Giới tính", "Nơi ở để học tập", "Họ và tên"]])
def test_missing_or_duplicate_required_columns_reject_file(xlsx, headers):
    from app.services.excel_service import ImportProblem
    with pytest.raises(ImportProblem) as exc:
        parse(xlsx([["A", "Nam", "Đường A"]], headers))
    assert exc.value.status_code == 422
    assert exc.value.errors[0].excel_row == 1


@pytest.mark.parametrize("rows", [[], [[None, None, None]]])
def test_empty_dataset_is_rejected(xlsx, rows):
    from app.services.excel_service import ImportProblem
    with pytest.raises(ImportProblem, match="sinh viên"):
        parse(xlsx(rows))


def test_trailing_empty_rows_do_not_create_students(xlsx):
    result = parse(xlsx([["A", "Nam", "Đường A"], [None, None, None]]))
    assert result.summary.total == 1


@pytest.mark.parametrize("content", [b"not excel", b"", b"PK\x03\x04broken"])
def test_corrupt_workbooks_are_rejected(content):
    from app.services.excel_service import ImportProblem
    with pytest.raises(ImportProblem) as exc:
        parse(content)
    assert exc.value.status_code == 400


def test_row_limit_rejects_instead_of_truncating(xlsx):
    from app.services.excel_service import ImportProblem
    rows = [["A", "Nam", "Đường A"], ["B", "Nữ", "Đường B"]]
    assert parse(xlsx(rows), max_rows=2).summary.total == 2
    with pytest.raises(ImportProblem, match="dòng"):
        parse(xlsx(rows), max_rows=1)


def test_formula_numeric_and_long_text_are_row_errors(xlsx):
    result = parse(xlsx([["=1+1", "Nam", "Đường A"], [123, "Nữ", "Đường B"], ["C", "Nam", "A" * 2001]]))
    assert len(result.students) == 3
    assert result.summary.invalid_rows == 3
    assert not result.can_proceed


def test_expanded_archive_limit(xlsx):
    from app.services.excel_service import ImportProblem
    with pytest.raises(ImportProblem, match="giải nén"):
        parse(xlsx([["A", "Nam", "Đường A"]]), max_uncompressed_bytes=100)


def test_excel_error_cells_are_retained_but_cannot_proceed(xlsx):
    result = parse(xlsx([["#VALUE!", "Nam", "#REF!"]]))
    assert len(result.students) == 1
    assert not result.can_proceed
    assert result.summary.invalid_rows == 1
    assert {(error.excel_row, error.field) for error in result.errors} == {
        (2, "Họ và tên"), (2, "Nơi ở để học tập"),
    }

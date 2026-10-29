from io import BytesIO
from pathlib import Path

import pytest
from openpyxl import load_workbook
from app.services.excel_service import parse_students, ImportProblem

TEMPLATE = Path(__file__).resolve().parents[1] / 'frontend/templates/danh-sach-sinh-vien.xlsx'


def test_template_is_blank_and_filled_copy_imports():
    content = TEMPLATE.read_bytes()
    book = load_workbook(BytesIO(content))
    sheet = book.worksheets[0]
    assert [c.value for c in sheet[1]] == ['Họ và tên', 'Giới tính', 'Nơi ở để học tập', 'Cư xá/Khu vực']
    assert len(book.worksheets) == 2
    assert any(d.type == 'list' and d.formula1 == '"Nam,Nữ"' for d in sheet.data_validations.dataValidation)
    with pytest.raises(ImportProblem, match='không có sinh viên'):
        parse_students(content)
    sheet.append(['Nguyễn Văn An', 'Nam', 'KTX Nông Lâm, TP.HCM', 'Cư xá A'])
    sheet.append(['Trần Thị Bình', 'Nữ', 'Linh Trung, TP.HCM', None])
    output = BytesIO()
    book.save(output)
    result = parse_students(output.getvalue())
    assert result.can_proceed
    assert result.summary.total == 2
    assert 'Cư xá A' in result.students[0].dia_chi_da_sua

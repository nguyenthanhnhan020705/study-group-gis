from io import BytesIO

import pytest
from openpyxl import Workbook


@pytest.fixture
def xlsx():
    def build(rows, headers=None):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Sinh_vien"
        sheet.append(headers if headers is not None else ["Họ và tên", "Giới tính", "Nơi ở để học tập"])
        for row in rows:
            sheet.append(row)
        stream = BytesIO()
        workbook.save(stream)
        workbook.close()
        return stream.getvalue()
    return build

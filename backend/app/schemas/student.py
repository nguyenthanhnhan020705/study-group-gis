from typing import Literal

from pydantic import BaseModel, Field


class Student(BaseModel):
    student_id: str
    excel_row: int
    ho_ten: str
    gioi_tinh: str
    dia_chi_goc: str
    dia_chi_da_sua: str | None = None
    vi_tri_dai_dien: str | None = None
    lat: float | None = None
    lon: float | None = None
    geocode_status: Literal["pending", "needs_review", "verified", "error"] = "pending"
    geocode_confidence: float | None = None
    location_confirmed: bool = False
    nhom: int | None = None


class ImportErrorDetail(BaseModel):
    excel_row: int | None = None
    student_id: str | None = None
    field: str
    message: str


class ImportSummary(BaseModel):
    total: int = 0
    male: int = 0
    female: int = 0
    invalid_rows: int = 0


class ImportResult(BaseModel):
    students: list[Student] = Field(default_factory=list)
    errors: list[ImportErrorDetail] = Field(default_factory=list)
    summary: ImportSummary = Field(default_factory=ImportSummary)
    can_proceed: bool = False
    worksheet: str | None = None

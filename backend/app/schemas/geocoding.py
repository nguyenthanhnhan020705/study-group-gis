from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GeocodeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: str = Field(min_length=1, max_length=80)
    address: str = Field(min_length=1, max_length=2000)

    @field_validator("student_id", "address")
    @classmethod
    def nonempty(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Không được để trống.")
        return value


class GeocodeBatch(BaseModel):
    students: list[GeocodeInput] = Field(min_length=1, max_length=5)

    @field_validator("students")
    @classmethod
    def unique_ids(cls, rows):
        if len({row.student_id for row in rows}) != len(rows):
            raise ValueError("student_id không được trùng trong một yêu cầu.")
        return rows


class Candidate(BaseModel):
    auto_selectable: bool = False
    lat: float | None = None
    lon: float | None = None
    formatted: str
    result_type: str
    confidence: float | None = None
    eligible: bool = False
    reason: str = ""
    source: Literal["geoapify_geocoding", "geoapify_places"] = "geoapify_geocoding"
    source_url: str | None = None
    address_source_url: str | None = None
    provider_formatted: str | None = None
    allowed_genders: list[Literal["Nam", "Nữ"]] | None = None


class GeocodeResult(BaseModel):
    student_id: str
    address: str
    status: Literal["needs_review", "error"] = "needs_review"
    candidates: list[Candidate] = Field(default_factory=list)
    message: str = ""
    error_code: str | None = None

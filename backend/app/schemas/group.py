"""Grouping accepts confirmed session data, with no UI-only candidate fields."""
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, StrictBool, StringConstraints, field_validator, model_validator

Text = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]
Identifier = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=80)]
Coordinate = Annotated[float, Field(strict=True, allow_inf_nan=False)]


class VerifiedStudent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    student_id: Identifier
    ho_ten: Text
    gioi_tinh: Literal["Nam", "Nữ"]
    dia_chi_goc: Text
    dia_chi_da_sua: Text | None = None
    vi_tri_dai_dien: Text
    excel_row: Annotated[int, Field(strict=True, ge=2)] | None = None
    lat: Annotated[Coordinate, Field(ge=-90, le=90)]
    lon: Annotated[Coordinate, Field(ge=-180, le=180)]
    geocode_status: Literal["verified"]
    location_confirmed: StrictBool
    geocode_confidence: Annotated[Coordinate, Field(ge=0, le=1)] | None = None

    @field_validator("location_confirmed")
    @classmethod
    def require_confirmation(cls, value):
        if not value:
            raise ValueError("Mọi sinh viên phải được xác nhận vị trí trước khi chia nhóm.")
        return value


class GenerateGroupsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    students: list[VerifiedStudent] = Field(min_length=1, max_length=1000)
    target_male: int = Field(strict=True, ge=0)
    target_female: int = Field(strict=True, ge=0)

    @model_validator(mode="after")
    def validate_grouping(self):
        if self.target_male + self.target_female == 0:
            raise ValueError("Tổng số Nam và Nữ mong muốn phải lớn hơn 0.")
        if len({row.student_id for row in self.students}) != len(self.students):
            raise ValueError("student_id không được trùng.")
        return self


class DistanceMetrics(BaseModel):
    pair_count: int = Field(ge=0)
    mean_distance_m: float = Field(ge=0, allow_inf_nan=False)
    max_distance_m: float = Field(ge=0, allow_inf_nan=False)


class Centroid(BaseModel):
    lat: float = Field(ge=-90, le=90, allow_inf_nan=False)
    lon: float = Field(ge=-180, le=180, allow_inf_nan=False)


class Group(BaseModel):
    group_id: int = Field(ge=1)
    members: list[VerifiedStudent] = Field(min_length=1)
    size: int = Field(ge=1)
    male: int = Field(ge=0)
    female: int = Field(ge=0)
    male_delta: int
    female_delta: int
    centroid: Centroid
    metrics: DistanceMetrics


class Assignment(BaseModel):
    student_id: str
    group_id: int


class GroupingWarning(BaseModel):
    code: str
    message: str
    group_ids: list[int] = Field(default_factory=list)


class GenerateGroupsResponse(BaseModel):
    k: int = Field(ge=1)
    target_male: int
    target_female: int
    seed: int
    strategy: str
    assignments: list[Assignment]
    groups: list[Group]
    overall_metrics: DistanceMetrics
    warnings: list[GroupingWarning]

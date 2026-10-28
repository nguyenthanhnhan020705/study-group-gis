"""Bound the submitted current grouping result before workbook generation."""
from pydantic import ConfigDict, Field

from app.schemas.group import Assignment, GenerateGroupsResponse, Group, GroupingWarning


class ExportGroupsRequest(GenerateGroupsResponse):
    model_config = ConfigDict(extra="forbid")
    k: int = Field(strict=True, ge=1, le=1000)
    target_male: int = Field(strict=True, ge=0)
    target_female: int = Field(strict=True, ge=0)
    assignments: list[Assignment] = Field(min_length=1, max_length=1000)
    groups: list[Group] = Field(min_length=1, max_length=1000)
    warnings: list[GroupingWarning] = Field(max_length=1000)

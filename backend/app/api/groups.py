"""CPU grouping runs in FastAPI's worker thread with a per-process job guard."""
from fastapi import APIRouter, Request
from starlette.responses import JSONResponse, Response

from app.schemas.group import GenerateGroupsRequest, GenerateGroupsResponse
from app.services.grouping_service import GroupingInvariantError, generate_groups
from app.schemas.export import ExportGroupsRequest
from app.services.export_service import ExportProblem, export_workbook

router = APIRouter(prefix="/api/groups", tags=["Chia nhóm"])


@router.post("/export")
def export(payload: ExportGroupsRequest, request: Request):
    if sum(len(group.members) for group in payload.groups) > request.app.state.settings.max_student_rows:
        return JSONResponse({"message": "Danh sách vượt số dòng cho phép của máy chủ."}, status_code=413)
    try:
        data = export_workbook(payload)
    except ExportProblem as exc:
        return JSONResponse({"message": str(exc)}, status_code=422)
    return Response(data, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={
        "Content-Disposition": 'attachment; filename="danh_sach_nhom.xlsx"',
        "Cache-Control": "no-store",
        "X-Content-Type-Options": "nosniff",
    })


@router.post("/generate", response_model=GenerateGroupsResponse)
def generate(payload: GenerateGroupsRequest, request: Request):
    settings = request.app.state.settings
    if len(payload.students) > settings.max_student_rows:
        return JSONResponse({"message": "Danh sách vượt số dòng cho phép của máy chủ."}, status_code=413)
    west, south, east, north = settings.geocoding_bounds
    if any(not (south <= row.lat <= north and west <= row.lon <= east) for row in payload.students):
        return JSONResponse({"message": "Vị trí sinh viên nằm ngoài vùng nghiên cứu cho phép."}, status_code=422)
    lock = request.app.state.grouping_lock
    if not lock.acquire(blocking=False):
        return JSONResponse({"message": "Máy chủ đang chia nhóm. Vui lòng thử lại sau."}, status_code=429)
    try:
        return generate_groups(payload)
    except (GroupingInvariantError, ValueError, ArithmeticError):
        return JSONResponse({"message": "Không tạo được kết quả chia nhóm hợp lệ. Vui lòng kiểm tra dữ liệu và thử lại."}, status_code=500)
    finally:
        lock.release()

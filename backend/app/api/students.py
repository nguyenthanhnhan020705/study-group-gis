from fastapi import APIRouter, Request
from starlette.concurrency import run_in_threadpool
from starlette.datastructures import UploadFile
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse

from app.schemas.student import ImportResult
from app.services.excel_service import ImportProblem, parse_students

router = APIRouter(prefix="/api/students", tags=["Sinh viên"])


@router.post("/import", response_model=ImportResult, openapi_extra={
    "requestBody": {"required": True, "content": {"multipart/form-data": {"schema": {
        "type": "object", "required": ["file"], "properties": {"file": {"type": "string", "format": "binary"}},
    }}}},
})
async def import_students(request: Request):
    settings = request.app.state.settings
    try:
        async with request.form(max_files=1, max_fields=0) as form:
            file = form.get("file")
            if not isinstance(file, UploadFile):
                raise ImportProblem("Vui lòng chọn một file Excel .xlsx.")
            if not (file.filename or "").lower().endswith(".xlsx"):
                raise ImportProblem("Chỉ hỗ trợ file .xlsx.", 400)
            content = await file.read(settings.max_upload_bytes + 1)
            if len(content) > settings.max_upload_bytes:
                raise ImportProblem(f"File vượt giới hạn {settings.max_upload_bytes} byte.", 413)
            return await run_in_threadpool(parse_students, content, max_rows=settings.max_student_rows)
    except HTTPException:
        problem = ImportProblem("Yêu cầu không hợp lệ. Chỉ tải một file .xlsx với trường file.", 400)
    except ImportProblem as exc:
        problem = exc
    return JSONResponse(ImportResult(errors=problem.errors).model_dump(), status_code=problem.status_code)

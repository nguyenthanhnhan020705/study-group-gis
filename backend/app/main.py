"""FastAPI entry point. Run with --app-dir backend from the repository root."""

from threading import Lock

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.core.config import Settings, load_settings
from app.core.upload_limit import UploadLimitMiddleware
from app.api.students import router as students_router
from app.api.geocoding import router as geocoding_router
from app.api.groups import router as groups_router
from app.services.geocoding_service import GeocodingService
from app.services.map_tiles import MapTileService
from app.api.map_tiles import router as map_tiles_router


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else load_settings()
    application = FastAPI(
        title="WebGIS chia nhóm học tập",
        description="API hỗ trợ giảng viên chia nhóm theo vị trí địa lý.",
        version="0.6.0",
    )
    application.state.settings = settings
    application.state.geocoding = GeocodingService(settings)
    application.state.map_tiles = MapTileService(settings)
    application.state.grouping_lock = Lock()
    application.include_router(students_router)
    application.include_router(geocoding_router)
    application.include_router(groups_router)
    application.include_router(map_tiles_router)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exc: RequestValidationError):
        if request.url.path not in {"/api/groups/generate", "/api/groups/export"}:
            return await request_validation_exception_handler(request, exc)
        # Never echo invalid raw floats (NaN/Infinity) or student payloads into JSON errors.
        details = [{"loc": item["loc"], "msg": item["msg"], "type": item["type"]} for item in exc.errors()]
        return JSONResponse({"message": "Dữ liệu chia nhóm không hợp lệ. Kiểm tra vị trí xác nhận và số Nam/Nữ.", "detail": details}, status_code=422)
    # Include a small allowance for multipart headers; enforce file bytes separately.
    application.add_middleware(UploadLimitMiddleware, max_bytes=settings.max_upload_bytes + 64 * 1024)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    @application.get("/api/health", tags=["Hệ thống"])
    async def health() -> dict[str, str]:
        # Liveness only: no credentials, configuration or external API calls.
        return {"status": "ok"}

    return application


app = create_app()

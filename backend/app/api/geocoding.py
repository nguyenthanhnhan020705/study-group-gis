from fastapi import APIRouter, Request
from starlette.responses import JSONResponse

from app.schemas.geocoding import GeocodeBatch, GeocodeInput, GeocodeResult
from app.services.geocoding_service import GeocodeProblem

router = APIRouter(prefix="/api/geocode", tags=["Vị trí"])


@router.post("/batch")
async def batch(payload: GeocodeBatch, request: Request):
    try:
        results = await request.app.state.geocoding.batch(payload.students)
        return {"results": results}
    except GeocodeProblem as exc:
        return JSONResponse({"message": str(exc)}, status_code=exc.status_code)


@router.post("/retry", response_model=GeocodeResult)
async def retry(payload: GeocodeInput, request: Request):
    try:
        return (await request.app.state.geocoding.batch([payload]))[0]
    except GeocodeProblem as exc:
        return JSONResponse({"message": str(exc)}, status_code=exc.status_code)

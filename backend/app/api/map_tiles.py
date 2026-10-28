from typing import Annotated

from fastapi import APIRouter, Path, Request
from starlette.responses import JSONResponse, Response

from app.services.map_tiles import MapTileProblem

router = APIRouter(prefix="/api/map", tags=["Bản đồ"])


@router.get("/tiles/{z}/{x}/{y}.png")
async def tile(z: Annotated[int, Path(ge=0, le=19)], x: Annotated[int, Path(ge=0)], y: Annotated[int, Path(ge=0)], request: Request):
    try:
        data = await request.app.state.map_tiles.get_tile(z, x, y)
    except MapTileProblem as exc:
        return JSONResponse({"message": str(exc)}, status_code=exc.status_code, headers={"Cache-Control": "no-store"})
    return Response(data, media_type="image/png", headers={"Cache-Control": "public, max-age=300", "X-Content-Type-Options": "nosniff"})

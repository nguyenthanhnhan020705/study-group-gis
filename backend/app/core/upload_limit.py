"""Bound request bytes before multipart parsing, including chunked requests."""

from starlette.responses import JSONResponse

from app.schemas.student import ImportErrorDetail, ImportResult


class UploadLimitMiddleware:
    def __init__(self, app, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] not in {"/api/students/import", "/api/geocode/batch", "/api/geocode/retry", "/api/groups/generate", "/api/groups/export"} or scope["method"] != "POST":
            return await self.app(scope, receive, send)
        limit = self.max_bytes if scope["path"] == "/api/students/import" else 8 * 1024 * 1024 if scope["path"] in {"/api/groups/generate", "/api/groups/export"} else 64 * 1024
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > limit:
                if scope["path"] in {"/api/groups/generate", "/api/groups/export"}:
                    return await JSONResponse({"message": "Yêu cầu chia nhóm vượt dung lượng cho phép (8 MiB)."}, status_code=413)(scope, receive, send)
                result = ImportResult(errors=[ImportErrorDetail(field="file", message="Yêu cầu tải lên vượt dung lượng cho phép.")])
                return await JSONResponse(result.model_dump(), status_code=413)(scope, receive, send)
            body.extend(chunk)
            if not message.get("more_body", False):
                break
        sent = False

        async def replay():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": bytes(body), "more_body": False}
            return await receive()

        await self.app(scope, replay, send)

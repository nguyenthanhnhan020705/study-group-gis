import asyncio
import base64

import httpx
import pytest
from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import create_app
from app.services.map_tiles import MapTileProblem, MapTileService

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADElEQVR4nGMw7ggFAAICARGASOjmAAAAAElFTkSuQmCC")


@pytest.mark.parametrize("blocked_queue", [False, True])
def test_total_deadline_covers_queue_and_slow_drip(monkeypatch, blocked_queue):
    monkeypatch.setattr("app.services.map_tiles.TILE_DEADLINE", 0.03)
    class Drip(httpx.AsyncByteStream):
        async def __aiter__(self):
            for byte in PNG:
                await asyncio.sleep(0.01)
                yield bytes([byte])
    tiles = service(lambda request: httpx.Response(200, stream=Drip(), headers={"Content-Type": "image/png"}))
    async def run():
        if blocked_queue:
            tiles.semaphore = asyncio.Semaphore(0)
        with pytest.raises(MapTileProblem):
            await asyncio.wait_for(tiles.get_tile(0, 0, 0), timeout=0.3)
        assert not tiles.cache
    asyncio.run(run())


def test_truncated_png_is_never_cached():
    tiles = service(lambda request: httpx.Response(200, content=PNG[:25], headers={"Content-Type": "image/png"}))
    with pytest.raises(MapTileProblem):
        asyncio.run(tiles.get_tile(0, 0, 0))
    assert not tiles.cache


def service(handler, key="private-test-key"):
    return MapTileService(Settings(cors_origins=(), geoapify_api_key=key), transport=httpx.MockTransport(handler))


def test_fixed_provider_url_keeps_key_in_backend_and_caches_only_valid_tiles(monkeypatch):
    calls = []
    now = [0.0]
    monkeypatch.setattr("app.services.map_tiles.monotonic", lambda: now[0])
    def handler(request):
        calls.append(request)
        assert request.url.host == "maps.geoapify.com"
        assert request.url.path == "/v1/tile/osm-carto/12/3263/1923.png"
        assert request.url.params["apiKey"] == "private-test-key"
        return httpx.Response(200, content=PNG, headers={"Content-Type": "image/png"})
    tiles = service(handler)
    async def run():
        assert await tiles.get_tile(12, 3263, 1923) == PNG
        assert await tiles.get_tile(12, 3263, 1923) == PNG
        assert len(calls) == 1
        now[0] = 301
        assert await tiles.get_tile(12, 3263, 1923) == PNG
        assert len(calls) == 2
    asyncio.run(run())


@pytest.mark.parametrize("coordinates", [(-1, 0, 0), (20, 0, 0), (0, 1, 0), (1, 0, 2), (1, -1, 0)])
def test_invalid_tile_coordinates_are_rejected_before_provider(coordinates):
    def forbidden(request):
        raise AssertionError("Invalid tile must never reach provider")
    with pytest.raises(MapTileProblem):
        asyncio.run(service(forbidden).get_tile(*coordinates))


def test_missing_key_never_calls_provider():
    def forbidden(request):
        raise AssertionError("No provider call without key")
    with pytest.raises(MapTileProblem) as exc:
        asyncio.run(service(forbidden, key="").get_tile(0, 0, 0))
    assert "Geoapify" in str(exc.value)


@pytest.mark.parametrize("status,content,kind", [
    (401, b"private-test-key", "application/json"),
    (403, b"private-test-key", "application/json"),
    (429, b"private-test-key", "application/json"),
    (500, b"private-test-key", "text/html"),
    (302, b"", "image/png"),
    (200, b"not an image", "image/png"),
    (200, PNG, "text/html"),
    (200, PNG + b"x" * (512 * 1024), "image/png"),
], ids=["unauthorized", "forbidden", "quota", "server", "redirect", "not-png", "wrong-type", "too-large"])
def test_upstream_errors_redirect_nonimage_and_oversize_are_sanitized(status, content, kind):
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(status, content=content, headers={"Content-Type": kind, "Location": "https://example.invalid/key=private-test-key"})
    tiles = service(handler)
    for _ in range(2):
        with pytest.raises(MapTileProblem) as exc:
            asyncio.run(tiles.get_tile(0, 0, 0))
        assert "private-test-key" not in str(exc.value) and "https://" not in str(exc.value)
    if status == 429:
        assert len(calls) == 1  # respect provider cooldown, no per-tile request storm
    else:
        assert len(calls) == 2  # failures never cached as successful images


def test_timeout_is_sanitized():
    def handler(request):
        raise httpx.ReadTimeout("private-test-key", request=request)
    with pytest.raises(MapTileProblem) as exc:
        asyncio.run(service(handler).get_tile(0, 0, 0))
    assert "private-test-key" not in str(exc.value)


def test_cache_is_bounded():
    calls = []
    def handler(request):
        calls.append(request)
        return httpx.Response(200, content=PNG, headers={"Content-Type": "image/png"})
    tiles = service(handler)
    async def run():
        for x in range(65):
            await tiles.get_tile(7, x, 0)
        await tiles.get_tile(7, 0, 0)
    asyncio.run(run())
    assert len(calls) == 66


def test_tile_endpoint_returns_only_image_and_sanitized_errors():
    app = create_app(Settings(cors_origins=("http://127.0.0.1:5500",)))
    app.state.map_tiles = service(lambda request: httpx.Response(200, content=PNG, headers={"Content-Type": "image/png"}))
    with TestClient(app) as client:
        response = client.get("/api/map/tiles/0/0/0.png", headers={"Origin": "http://127.0.0.1:5500"})
        assert response.status_code == 200 and response.content == PNG
        assert response.headers["content-type"] == "image/png"
        assert response.headers["cache-control"] == "public, max-age=300"
        assert response.headers["access-control-allow-origin"] == "http://127.0.0.1:5500"
        assert "private-test-key" not in str(response.headers)
        assert client.get("/api/map/tiles/0/1/0.png").status_code == 422
        assert client.get("/api/map/tiles/20/0/0.png").status_code == 422
        app.state.map_tiles = service(lambda request: httpx.Response(403, text="private-test-key"))
        response = client.get("/api/map/tiles/0/0/0.png")
        assert response.status_code == 503 and "private-test-key" not in response.text
        assert response.headers["cache-control"] == "no-store"

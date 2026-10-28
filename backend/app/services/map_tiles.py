"""Fixed Geoapify raster source, with bounded public-tile cache and safe failures."""
import asyncio
from collections import OrderedDict
from time import monotonic

import httpx
import struct
import zlib

MAX_TILE_BYTES = 512 * 1024
CACHE_TTL = 300
MAX_CACHED_TILES = 64
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
TILE_DEADLINE = 10


def valid_png(data):
    if not data.startswith(PNG_SIGNATURE):
        return False
    offset, image_data, header = 8, False, False
    while offset + 12 <= len(data):
        size = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + size
        if end > len(data):
            return False
        kind = bytes(data[offset + 4:offset + 8])
        chunk = data[offset + 4:offset + 8 + size]
        if zlib.crc32(chunk) != struct.unpack_from(">I", data, end - 4)[0]:
            return False
        if not header:
            if kind != b"IHDR" or size != 13:
                return False
            width, height = struct.unpack_from(">II", data, offset + 8)
            if not 0 < width <= 512 or not 0 < height <= 512:
                return False
            header = True
        if kind == b"IDAT":
            image_data = True
        if kind == b"IEND":
            return size == 0 and end == len(data) and image_data
        offset = end
    return False


class MapTileProblem(Exception):
    def __init__(self, message, status_code=503):
        super().__init__(message)
        self.status_code = status_code


class MapTileService:
    def __init__(self, settings, transport=None):
        self.settings = settings
        self.transport = transport
        self.cache = OrderedDict()
        self.semaphore = asyncio.Semaphore(8)
        self.cooldown_until = 0.0

    async def get_tile(self, z: int, x: int, y: int) -> bytes:
        try:
            return await asyncio.wait_for(self._get_tile(z, x, y), timeout=TILE_DEADLINE)
        except TimeoutError:
            raise MapTileProblem("Quá thời gian tải ảnh nền. Vui lòng thử lại.") from None

    async def _get_tile(self, z: int, x: int, y: int) -> bytes:
        if not 0 <= z <= 19 or not 0 <= x < 2 ** z or not 0 <= y < 2 ** z:
            raise MapTileProblem("Tọa độ ảnh nền không hợp lệ.", 422)
        key = (z, x, y)
        cached = self.cache.get(key)
        if cached and monotonic() - cached[0] < CACHE_TTL:
            self.cache.move_to_end(key)
            return cached[1]
        if not self.settings.geoapify_api_key or self.settings.geoapify_api_key == "replace_with_your_own_key":
            raise MapTileProblem("Backend chưa cấu hình khóa Geoapify cho bản đồ dự phòng.")
        if monotonic() < self.cooldown_until:
            raise MapTileProblem("Nguồn bản đồ đang giới hạn truy cập. Vui lòng thử lại sau.")
        async with self.semaphore:
            # A queued request may reuse a just-completed tile or see a new cooldown.
            cached = self.cache.get(key)
            if cached and monotonic() - cached[0] < CACHE_TTL:
                self.cache.move_to_end(key)
                return cached[1]
            if monotonic() < self.cooldown_until:
                raise MapTileProblem("Nguồn bản đồ đang giới hạn truy cập. Vui lòng thử lại sau.")
            try:
                async with httpx.AsyncClient(timeout=8, transport=self.transport, follow_redirects=False) as client:
                    async with client.stream("GET", f"https://maps.geoapify.com/v1/tile/osm-carto/{z}/{x}/{y}.png",
                                             params={"apiKey": self.settings.geoapify_api_key}) as response:
                        if response.status_code == 429:
                            self.cooldown_until = monotonic() + 30
                        if response.status_code != 200 or response.headers.get("content-type", "").split(";")[0].strip().lower() != "image/png":
                            raise MapTileProblem("Không tải được ảnh nền từ nguồn dự phòng. Vui lòng thử lại sau.")
                        data = bytearray()
                        async for chunk in response.aiter_bytes():
                            if len(data) + len(chunk) > MAX_TILE_BYTES:
                                raise MapTileProblem("Ảnh nền vượt dung lượng cho phép.")
                            data.extend(chunk)
            except httpx.HTTPError:
                # HTTP exceptions include credential-bearing URLs; never echo or log them.
                raise MapTileProblem("Không kết nối được nguồn bản đồ dự phòng. Vui lòng thử lại sau.") from None
        if not valid_png(data):
            raise MapTileProblem("Nguồn bản đồ trả ảnh không hợp lệ.")
        image = bytes(data)
        self.cache[key] = (monotonic(), image)
        self.cache.move_to_end(key)
        while len(self.cache) > MAX_CACHED_TILES:
            self.cache.popitem(last=False)
        return image

"""Read backend configuration without mutating the process environment."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
LOCAL_ORIGINS = "http://127.0.0.1:5500,http://localhost:5500"


@dataclass(frozen=True)
class Settings:
    cors_origins: tuple[str, ...]
    geocoding_country: str = "vn"
    geoapify_api_key: str = field(default="", repr=False)
    max_upload_bytes: int = 5 * 1024 * 1024
    max_student_rows: int = 1000
    geocoding_timeout: float = 8.0
    geocoding_interval: float = 1.0
    geocoding_min_confidence: float = 0.7
    geocoding_bounds: tuple[float, float, float, float] = (106.4, 10.5, 107.0, 11.2)


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    values = {**dotenv_values(env_file, encoding="utf-8-sig"), **os.environ}
    origins = tuple(item.strip() for item in (values.get("CORS_ORIGINS") or "").split(","))
    if "CORS_ORIGINS" not in values:
        origins = tuple(LOCAL_ORIGINS.split(","))
    for origin in origins:
        parsed = urlsplit(origin)
        if (
            parsed.scheme not in ("http", "https")
            or not parsed.hostname
            or "*" in origin
            or any(char.isspace() for char in origin)
            or parsed.username is not None
            or parsed.password is not None
            or parsed.path
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("CORS_ORIGINS phải chứa các origin HTTP(S) cụ thể, không có đường dẫn hoặc wildcard.")
    return Settings(
        cors_origins=origins,
        geocoding_country=values.get("GEOCODING_COUNTRY") or "vn",
        geoapify_api_key=values.get("GEOAPIFY_API_KEY") or "",
        max_upload_bytes=_positive_integer(values, "MAX_UPLOAD_BYTES", 5 * 1024 * 1024),
        max_student_rows=_positive_integer(values, "MAX_STUDENT_ROWS", 1000),
        geocoding_timeout=_number(values, "GEOCODING_TIMEOUT", 8, 1, 30),
        geocoding_interval=_number(values, "GEOCODING_INTERVAL", 1, 0.35, 10),
        geocoding_min_confidence=_number(values, "GEOCODING_MIN_CONFIDENCE", 0.7, 0, 1),
        geocoding_bounds=_bounds(values.get("GEOCODING_BOUNDS", "106.4,10.5,107.0,11.2")),
    )


def _positive_integer(values: dict, name: str, default: int) -> int:
    try:
        value = int(values.get(name, str(default)))
    except (TypeError, ValueError):
        raise ValueError(f"{name} phải là số nguyên dương.") from None
    if value <= 0:
        raise ValueError(f"{name} phải là số nguyên dương.")
    return value


def _number(values, name, default, minimum, maximum):
    try:
        value = float(values.get(name, default))
        if not minimum <= value <= maximum:
            raise ValueError
        return value
    except (ValueError, TypeError):
        raise ValueError(f"{name} phải nằm trong khoảng {minimum}–{maximum}.") from None


def _bounds(value):
    try:
        west, south, east, north = map(float, value.split(","))
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError
        return west, south, east, north
    except (ValueError, TypeError, AttributeError):
        raise ValueError("GEOCODING_BOUNDS phải là west,south,east,north hợp lệ.") from None

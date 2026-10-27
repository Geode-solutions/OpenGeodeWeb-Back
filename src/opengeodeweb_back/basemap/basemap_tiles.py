from __future__ import annotations

# Standard library imports
import contextlib
import hashlib
import http.client
import math
import os
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

# Local application imports
from opengeodeweb_back.basemap.basemap_providers import _url_template, tile_url

HALF_WORLD = 20037508.342789244
MAX_ZOOM = 19
FETCH_WORKERS = 8
FETCH_TIMEOUT_SECONDS = 10
# IncompleteRead and other HTTPException are not OSError
DOWNLOAD_ERRORS = (OSError, http.client.HTTPException)


@dataclass(frozen=True)
class TileRange:
    z: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def tile_span(self) -> float:
        return 2 * HALF_WORLD / (1 << self.z)

    def bounds_3857(self) -> tuple[float, float, float, float]:
        span = self.tile_span()
        # Tile rows grow southward from the north edge of the world
        return (
            -HALF_WORLD + self.x_min * span,
            HALF_WORLD - (self.y_max + 1) * span,
            -HALF_WORLD + (self.x_max + 1) * span,
            HALF_WORLD - self.y_min * span,
        )

    def tiles(self) -> list[tuple[int, int]]:
        return [
            (x, y)
            for x in range(self.x_min, self.x_max + 1)
            for y in range(self.y_min, self.y_max + 1)
        ]


def _range_at(bounds_3857: tuple[float, float, float, float], z: int) -> TileRange:
    span = 2 * HALF_WORLD / (1 << z)
    last = (1 << z) - 1
    x_min, y_min, x_max, y_max = bounds_3857

    def column(x: float) -> int:
        return min(last, max(0, math.floor((x + HALF_WORLD) / span)))

    def row(y: float) -> int:
        return min(last, max(0, math.floor((HALF_WORLD - y) / span)))

    return TileRange(z, column(x_min), column(x_max), row(y_max), row(y_min))


def tile_range(
    bounds_3857: tuple[float, float, float, float], tile_size: int, max_pixels: int = 2048
) -> TileRange:
    """Most detailed tile range whose mosaic side stays within max_pixels."""
    best = _range_at(bounds_3857, 0)
    for z in range(1, MAX_ZOOM + 1):
        candidate = _range_at(bounds_3857, z)
        columns = candidate.x_max - candidate.x_min + 1
        rows = candidate.y_max - candidate.y_min + 1
        if max(columns, rows) * tile_size > max_pixels:
            break
        best = candidate
    return best


def _cache_folder() -> Path:
    default = Path(tempfile.gettempdir()) / "opengeodeweb_basemap_cache"
    return Path(os.environ.get("BASEMAP_CACHE_FOLDER", str(default)))


def _is_image(content: bytes) -> bool:
    # Error pages come back as HTTP 200 with a text body
    return content.startswith((b"\x89PNG", b"\xff\xd8"))


def _read_cache(cached: Path) -> bytes | None:
    try:
        content = cached.read_bytes()
    except OSError:
        return None
    # A file broken by a crash or a disk error is downloaded again
    return content if _is_image(content) else None


def _write_cache(cached: Path, content: bytes) -> None:
    # Best effort: a tile that cannot be cached is still used
    try:
        cached.parent.mkdir(parents=True, exist_ok=True)
        descriptor, temporary = tempfile.mkstemp(dir=cached.parent, prefix=f".{cached.name}.")
    except OSError:
        return
    try:
        with os.fdopen(descriptor, "wb") as file:
            file.write(content)
        # Atomic: a concurrent build never reads a half-written tile
        Path(temporary).replace(cached)
    except OSError:
        with contextlib.suppress(OSError):
            Path(temporary).unlink()


def _fetch_tile(style: str, z: int, x: int, y: int) -> bytes | None:
    # The template hash keeps tiles of different providers apart
    template_hash = hashlib.sha256(_url_template(style).encode()).hexdigest()[:12]
    cached = _cache_folder() / style / template_hash / str(z) / str(x) / str(y)
    cached_content = _read_cache(cached)
    if cached_content is not None:
        return cached_content
    try:
        # URL comes from the provider table or the environment
        url = tile_url(style, z, x, y)
        with urllib.request.urlopen(url, timeout=FETCH_TIMEOUT_SECONDS) as response:  # noqa: S310
            content: bytes = response.read()
    except DOWNLOAD_ERRORS:
        return None
    if not _is_image(content):
        return None
    _write_cache(cached, content)
    return content


def fetch_tiles(style: str, tiles: TileRange) -> dict[tuple[int, int], bytes | None]:
    # The key check runs once, before any thread starts
    tile_url(style, tiles.z, tiles.x_min, tiles.y_min)
    with ThreadPoolExecutor(FETCH_WORKERS) as executor:
        contents = executor.map(lambda tile: _fetch_tile(style, tiles.z, *tile), tiles.tiles())
        return dict(zip(tiles.tiles(), contents, strict=True))


def _extension(content: bytes) -> str:
    # The viewer picks its image reader from the file extension
    return "png" if content.startswith(b"\x89PNG") else "jpg"


def save_tiles(tiles: TileRange, images: dict[tuple[int, int], bytes | None], folder: Path) -> None:
    """Writes each tile as <column>_<row>.<ext>, counted from the north-west corner."""
    folder.mkdir(parents=True, exist_ok=True)
    for (x, y), content in images.items():
        if content is not None:
            name = f"{x - tiles.x_min}_{y - tiles.y_min}.{_extension(content)}"
            (folder / name).write_bytes(content)

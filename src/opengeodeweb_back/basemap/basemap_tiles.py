from __future__ import annotations

# Standard library imports
import contextlib
import hashlib
import http.client
import io
import math
import os
import ssl
import tempfile
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

# Third party imports
import certifi
from PIL import Image

# Local application imports
from opengeodeweb_back.basemap.basemap_providers import (
    SOURCES,
    TILE_SIZE,
    USER_AGENT,
    tile_url,
    url_template,
)

HALF_WORLD = 20037508.342789244
MAX_ZOOM = 19
FETCH_WORKERS = 8
FETCH_TIMEOUT_SECONDS = 10
# IncompleteRead and other HTTPException are not OSError
DOWNLOAD_ERRORS = (OSError, http.client.HTTPException)
# Packaged binaries ship their own OpenSSL, which may not find the system certificates
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


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
    bounds_3857: tuple[float, float, float, float],
    tile_size: int,
    max_pixels: int = 2048,
    max_zoom: int = MAX_ZOOM,
) -> TileRange:
    """Most detailed tile range whose mosaic side stays within max_pixels."""
    best = _range_at(bounds_3857, 0)
    for z in range(1, max_zoom + 1):
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


def _fetch_tile(source: str, z: int, x: int, y: int) -> bytes | None:
    # The template hash keeps tiles of an overridden URL apart
    template_hash = hashlib.sha256(url_template(source).encode()).hexdigest()[:12]
    cached = _cache_folder() / source / template_hash / str(z) / str(x) / str(y)
    cached_content = _read_cache(cached)
    if cached_content is not None:
        return cached_content
    # Open tile servers ask every application to name itself
    request = urllib.request.Request(  # noqa: S310 URL from the source table or the environment
        tile_url(source, z, x, y), headers={"User-Agent": USER_AGENT}
    )
    try:
        with urllib.request.urlopen(  # noqa: S310
            request, timeout=FETCH_TIMEOUT_SECONDS, context=SSL_CONTEXT
        ) as response:
            content: bytes = response.read()
    except DOWNLOAD_ERRORS:
        return None
    if not _is_image(content):
        return None
    _write_cache(cached, content)
    return content


def _overzoomed(parent: bytes | None, depth: int, x: int, y: int) -> bytes | None:
    """The sub-square of a parent tile that covers tile (x, y), `depth` zooms deeper."""
    if parent is None:
        return None
    side = TILE_SIZE >> depth
    left = (x % (1 << depth)) * side
    top = (y % (1 << depth)) * side
    with Image.open(io.BytesIO(parent)) as image:
        # Same mode as the parent: transparent tiles stay transparent
        part = image.crop((left, top, left + side, top + side)).resize(
            (TILE_SIZE, TILE_SIZE), Image.Resampling.BILINEAR
        )
    output = io.BytesIO()
    part.save(output, format="PNG")
    return output.getvalue()


def fetch_tiles(source: str, tiles: TileRange) -> dict[tuple[int, int], bytes | None]:
    # Past its max zoom a source has no tile: its parent tiles are enlarged instead
    depth = max(0, tiles.z - SOURCES[source].max_zoom)
    z = tiles.z - depth
    parents = sorted({(x >> depth, y >> depth) for x, y in tiles.tiles()})
    with ThreadPoolExecutor(FETCH_WORKERS) as executor:
        contents = executor.map(lambda parent: _fetch_tile(source, z, *parent), parents)
        downloaded = dict(zip(parents, contents, strict=True))
    if depth == 0:
        return {tile: downloaded[tile] for tile in tiles.tiles()}
    return {
        (x, y): _overzoomed(downloaded[(x >> depth, y >> depth)], depth, x, y)
        for x, y in tiles.tiles()
    }


def fetch_sources(
    sources: list[str], tiles: TileRange
) -> dict[str, dict[tuple[int, int], bytes | None]]:
    """Every source at once: the slowest server sets the wait, not the sum of them."""
    with ThreadPoolExecutor(max(1, len(sources))) as executor:
        downloads = executor.map(lambda source: fetch_tiles(source, tiles), sources)
        return dict(zip(sources, downloads, strict=True))


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

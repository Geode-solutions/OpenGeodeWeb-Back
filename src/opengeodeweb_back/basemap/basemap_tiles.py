from __future__ import annotations

# Standard library imports
import contextlib
import hashlib
import http.client
import io
import logging
import math
import os
import ssl
import tempfile
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import certifi
from PIL import Image, ImageChops

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.basemap.basemap_providers import (
    SOURCES,
    TILE_SIZE,
    USER_AGENT,
    url_template,
)
from opengeodeweb_back.crs.crs_functions import WEB_MERCATOR, WGS84, convert_xy_corners

if TYPE_CHECKING:
    from collections.abc import Iterator

    from opengeodeweb_back.basemap.basemap_providers import Layer

logger = logging.getLogger(__name__)

# Folder of a basemap data holding its tiles: only basemaps have one
TILES_FOLDER = "tiles"
HALF_WORLD = 20037508.342789244
# Radius of the Web Mercator sphere: HALF_WORLD = pi * EARTH_RADIUS
EARTH_RADIUS = 6_378_137.0
# Scale denominator of a zoom 0 tile at the equator, for 0.28 mm screen pixels (OGC)
EQUATOR_SCALE_AT_ZOOM_0 = 559_082_264.0
DEFAULT_MAX_PIXELS = 2048
PNG_SIGNATURE = b"\x89PNG"
JPEG_QUALITY = 90
# Levels a JPEG may blur a plain colour by
JPEG_TOLERANCE = 3
TOO_MANY_REQUESTS_RETRIES = 2
MAX_RETRY_WAIT_SECONDS = 5.0
# One warning per source and per minute: a broken server must not flood the log
WARNING_INTERVAL_SECONDS = 60.0
# Cached in place of a tile the server does not have, so it is not asked again
MISSING_TILE = b"missing"
FETCH_WORKERS = 8
MAX_REQUESTS_PER_HOST = 8
FETCH_TIMEOUT_SECONDS = 10
# Whole download of a build: a hanging server must not hold the request for minutes
FETCH_DEADLINE_SECONDS = 30
# IncompleteRead and other HTTPException are not OSError
DOWNLOAD_ERRORS = (OSError, http.client.HTTPException)
# Packaged binaries ship their own OpenSSL, which may not find the system certificates
SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


_HOST_LIMITS: dict[str, threading.Semaphore] = {}
_HOST_LIMITS_LOCK = threading.Lock()
_LAST_WARNINGS: dict[str, float] = {}


def _host_limit(url: str) -> threading.Semaphore:
    # Sources fetched in parallel share the connections their server accepts
    host = urllib.parse.urlparse(url).netloc
    with _HOST_LIMITS_LOCK:
        return _HOST_LIMITS.setdefault(host, threading.Semaphore(MAX_REQUESTS_PER_HOST))


def _tile_span(z: int) -> float:
    return 2 * HALF_WORLD / (1 << z)


@dataclass(frozen=True)
class TileRange:
    z: int
    x_min: int
    x_max: int
    y_min: int
    y_max: int

    def bounds_3857(self) -> tuple[float, float, float, float]:
        span = _tile_span(self.z)
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


def tile_scale(z: int, y: int) -> float:
    """Scale denominator at the centre of tile row y: finer away from the equator."""
    center_y = HALF_WORLD - (y + 0.5) * _tile_span(z)
    # Web Mercator stretches the ground by 1 / cos(latitude) = cosh(y / R)
    return EQUATOR_SCALE_AT_ZOOM_0 / (1 << z) / math.cosh(center_y / EARTH_RADIUS)


def eligible(source: str, z: int, tile: tuple[int, int]) -> bool:
    """Whether the scale window and the area of a source hold the tile."""
    settings = SOURCES[source]
    if not settings.min_scale <= tile_scale(z, tile[1]) < settings.max_scale:
        return False
    if settings.area_3857 is None:
        return True
    x_min, y_min, x_max, y_max = TileRange(z, tile[0], tile[0], tile[1], tile[1]).bounds_3857()
    area_x_min, area_y_min, area_x_max, area_y_max = settings.area_3857
    return x_min < area_x_max and area_x_min < x_max and y_min < area_y_max and area_y_min < y_max


def _range_at(bounds_3857: tuple[float, float, float, float], z: int) -> TileRange:
    span = _tile_span(z)
    last = (1 << z) - 1
    x_min, y_min, x_max, y_max = bounds_3857

    def column(x: float) -> int:
        return min(last, max(0, math.floor((x + HALF_WORLD) / span)))

    def row(y: float) -> int:
        return min(last, max(0, math.floor((HALF_WORLD - y) / span)))

    return TileRange(z, column(x_min), column(x_max), row(y_max), row(y_min))


def tile_range(
    bounds_3857: tuple[float, float, float, float],
    max_zoom: int,
    max_pixels: int = DEFAULT_MAX_PIXELS,
) -> TileRange:
    """Most detailed tile range whose mosaic side stays within max_pixels."""
    best = _range_at(bounds_3857, 0)
    for z in range(1, max_zoom + 1):
        candidate = _range_at(bounds_3857, z)
        columns = candidate.x_max - candidate.x_min + 1
        rows = candidate.y_max - candidate.y_min + 1
        if max(columns, rows) * TILE_SIZE > max_pixels:
            break
        best = candidate
    return best


def tile_bbox(source: str, z: int, x: int, y: int) -> str:
    """Bounding box of tile z/x/y in the {bbox} CRS of the source."""
    bounds = TileRange(z, x, x, y, y).bounds_3857()
    crs = SOURCES[source].bbox_crs
    if crs is None or crs == "EPSG:3857":
        return ",".join(str(value) for value in bounds)
    # The CRS API converts the corners: no projection written here
    corners = convert_xy_corners(bounds, WEB_MERCATOR, WGS84)
    lons = [lon for lon, _ in corners]
    lats = [lat for _, lat in corners]
    lon_lat = (min(lons), min(lats), max(lons), max(lats))
    # WMS 1.3.0 reads EPSG:4326 latitude first
    if crs == "EPSG:4326":
        lon_lat = (lon_lat[1], lon_lat[0], lon_lat[3], lon_lat[2])
    return ",".join(str(value) for value in lon_lat)


def _cache_folder() -> Path:
    default = Path(tempfile.gettempdir()) / "opengeodeweb_basemap_cache"
    return Path(os.environ.get("BASEMAP_CACHE_FOLDER", str(default)))


def _is_image(content: bytes) -> bool:
    # Error pages come back as HTTP 200 with a text body
    return content.startswith((PNG_SIGNATURE, b"\xff\xd8"))


def _read_cache(cached: Path) -> bytes | None:
    try:
        content = cached.read_bytes()
    except OSError:
        return None
    # A file broken by a crash or a disk error is downloaded again
    return content if content == MISSING_TILE or _is_image(content) else None


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


def is_empty(content: bytes, empty_tile: str) -> bool:
    """Whether a served tile is the image the server sends where it has no data."""
    if empty_tile == "404":
        return False
    try:
        with Image.open(io.BytesIO(content)) as image:
            if empty_tile == "transparent":
                # No bounding box: every pixel has a zero alpha
                return image.convert("RGBA").getchannel("A").getbbox() is None
            rgb = image.convert("RGB")
    except OSError:  # UnidentifiedImageError included
        return False
    colour = tuple(int(empty_tile[i : i + 2], 16) for i in (1, 3, 5))
    difference = ImageChops.difference(rgb, Image.new("RGB", rgb.size, colour))
    # JPEG blurs a plain colour by a few levels: only larger differences count
    beyond = difference.point(lambda level: 255 if level > JPEG_TOLERANCE else 0)
    return beyond.getbbox() is None


def _warn_failure(source: str, reason: str) -> None:
    now = time.monotonic()
    with _HOST_LIMITS_LOCK:
        if now - _LAST_WARNINGS.get(source, -math.inf) < WARNING_INTERVAL_SECONDS:
            return
        _LAST_WARNINGS[source] = now
    logger.warning("Basemap source %s failed (%s): the next source is used", source, reason)


def _retry_wait(error: urllib.error.HTTPError) -> float:
    try:
        wait_seconds = float(error.headers.get("Retry-After", "1"))
    except ValueError:  # an HTTP date: wait the most
        wait_seconds = MAX_RETRY_WAIT_SECONDS
    return min(max(wait_seconds, 0.0), MAX_RETRY_WAIT_SECONDS)


def _download(url: str) -> bytes:
    # Open tile servers ask every application to name itself
    request = urllib.request.Request(  # noqa: S310 URL from the source table or the environment
        url, headers={"User-Agent": USER_AGENT}
    )
    with (
        _host_limit(url),
        urllib.request.urlopen(  # noqa: S310
            request, timeout=FETCH_TIMEOUT_SECONDS, context=SSL_CONTEXT
        ) as response,
    ):
        content: bytes = response.read()
    return content


def _fetch_tile(source: str, z: int, x: int, y: int, bbox: str) -> bytes | None:
    # The template hash keeps tiles of an overridden URL apart
    template = url_template(source)
    template_hash = hashlib.sha256(template.encode()).hexdigest()[:12]
    cached = _cache_folder() / source / template_hash / str(z) / str(x) / str(y)
    cached_content = _read_cache(cached)
    if cached_content is not None:
        return None if cached_content == MISSING_TILE else cached_content
    url = template.format(z=z, x=x, y=y, bbox=bbox)
    content = b""
    for attempt in range(TOO_MANY_REQUESTS_RETRIES + 1):
        try:
            content = _download(url)
            break
        except urllib.error.HTTPError as error:
            error.close()
            if error.code == HTTPStatus.TOO_MANY_REQUESTS and attempt < TOO_MANY_REQUESTS_RETRIES:
                time.sleep(_retry_wait(error))
                continue
            # Outside its area (the IGN outside France) a server answers 404: unlike a timeout or a
            # network error, asking again would give the same answer
            if error.code == HTTPStatus.NOT_FOUND:
                _write_cache(cached, MISSING_TILE)
            else:
                _warn_failure(source, f"HTTP {error.code}")
            return None
        except DOWNLOAD_ERRORS as error:
            _warn_failure(source, type(error).__name__)
            return None
    if not _is_image(content):
        return None
    # Where a server has no data it may send a plain tile instead of a 404: missing as well
    if is_empty(content, SOURCES[source].empty_tile):
        _write_cache(cached, MISSING_TILE)
        return None
    _write_cache(cached, content)
    return content


def _overzoomed(
    parent: bytes | None, depth: int, children: list[tuple[int, int]]
) -> dict[tuple[int, int], bytes | None]:
    """The sub-squares of a parent tile covering its children, `depth` zooms deeper."""
    if parent is None:
        return dict.fromkeys(children)
    side = TILE_SIZE >> depth
    images: dict[tuple[int, int], bytes | None] = {}
    try:
        # Decoded once for all its children
        with Image.open(io.BytesIO(parent)) as opened:
            transparent = opened.mode in ("RGBA", "LA", "PA") or "transparency" in opened.info
            # Palette and bilevel modes ignore BILINEAR: they become true colour first
            image = opened.convert("RGBA" if transparent else "RGB")
        # Opaque tiles stay JPEG: smaller and faster to encode than PNG, which ignores the quality
        image_format = "PNG" if transparent else "JPEG"
        for x, y in children:
            left = (x % (1 << depth)) * side
            top = (y % (1 << depth)) * side
            part = image.crop((left, top, left + side, top + side)).resize(
                (TILE_SIZE, TILE_SIZE), Image.Resampling.BILINEAR
            )
            output = io.BytesIO()
            part.save(output, format=image_format, quality=JPEG_QUALITY)
            images[(x, y)] = output.getvalue()
    except OSError:  # UnidentifiedImageError included
        return dict.fromkeys(children)
    return images


@contextlib.contextmanager
def _downloads(workers: int) -> Iterator[ThreadPoolExecutor]:
    executor = ThreadPoolExecutor(workers)
    try:
        yield executor
    finally:
        # Past the deadline the requests still running end on their own: the build does not wait
        executor.shutdown(wait=False, cancel_futures=True)


def _source_tiles(
    source: str,
    tiles: TileRange,
    downloads: ThreadPoolExecutor,
    deadline: float,
    wanted: list[tuple[int, int]] | None = None,
) -> dict[tuple[int, int], bytes | None]:
    # Past its max zoom a source has no tile: its parent tiles are enlarged instead
    depth = max(0, tiles.z - SOURCES[source].max_zoom)
    z = tiles.z - depth
    children: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for x, y in wanted or tiles.tiles():
        children.setdefault((x >> depth, y >> depth), []).append((x, y))
    # PROJ runs through OpenGeode: the bounding boxes are converted here, not in the downloads
    futures = {
        parent: downloads.submit(_fetch_tile, source, z, *parent, tile_bbox(source, z, *parent))
        for parent in children
    }
    done, _ = wait(futures.values(), timeout=max(0.0, deadline - time.monotonic()))
    images: dict[tuple[int, int], bytes | None] = {}
    for parent, future in futures.items():
        # An unfinished tile counts as missing
        content = future.result() if future in done else None
        if depth == 0:
            images[parent] = content
        else:
            images |= _overzoomed(content, depth, children[parent])
    return images


def fetch_tiles(source: str, tiles: TileRange) -> dict[tuple[int, int], bytes | None]:
    with _downloads(FETCH_WORKERS) as downloads:
        return _source_tiles(source, tiles, downloads, time.monotonic() + FETCH_DEADLINE_SECONDS)


def _first_served(
    layer: Layer, tiles: TileRange, downloads: ThreadPoolExecutor, deadline: float
) -> tuple[str, dict[tuple[int, int], bytes | None]] | None:
    for source in layer.sources:
        images = _source_tiles(source, tiles, downloads, deadline)
        if any(images.values()):
            return source, images
    return None


def _each_tile_served(
    layer: Layer, tiles: TileRange, downloads: ThreadPoolExecutor, deadline: float
) -> dict[str, dict[tuple[int, int], bytes | None]]:
    """Each tile from the first source serving it, the sources in the layer order."""
    missing = set(tiles.tiles())
    served: dict[str, dict[tuple[int, int], bytes | None]] = {}
    for source in layer.sources:
        wanted = sorted(tile for tile in missing if eligible(source, tiles.z, tile))
        if not wanted:
            continue
        images = _source_tiles(source, tiles, downloads, deadline, wanted)
        found: dict[tuple[int, int], bytes | None] = {
            tile: content for tile, content in images.items() if content is not None
        }
        if found:
            served[source] = found
            missing -= found.keys()
        if not missing:
            break
    return served


def fetch_layers(
    layers: list[Layer], tiles: TileRange
) -> dict[str, dict[tuple[int, int], bytes | None]]:
    """The tiles of each layer by source: the first source serving any, or tile by tile.

    Every layer at once: the slowest server sets the wait, not the sum of them.
    """
    deadline = time.monotonic() + FETCH_DEADLINE_SECONDS
    with (
        _downloads(FETCH_WORKERS * max(1, len(layers))) as downloads,
        ThreadPoolExecutor(max(1, len(layers))) as executor,
    ):

        def fetch(layer: Layer) -> dict[str, dict[tuple[int, int], bytes | None]]:
            if layer.tile_by_tile:
                return _each_tile_served(layer, tiles, downloads, deadline)
            first = _first_served(layer, tiles, downloads, deadline)
            return {} if first is None else dict([first])

        return {
            source: images
            for served in executor.map(fetch, layers)
            for source, images in served.items()
        }


def _extension(content: bytes) -> str:
    # The viewer picks its image reader from the file extension
    return "png" if content.startswith(PNG_SIGNATURE) else "jpg"


def save_tiles(tiles: TileRange, images: dict[tuple[int, int], bytes | None], folder: Path) -> None:
    """Writes each tile as <column>_<row>.<ext>, counted from the north-west corner."""
    folder.mkdir(parents=True, exist_ok=True)
    for (x, y), content in images.items():
        if content is not None:
            name = f"{x - tiles.x_min}_{y - tiles.y_min}.{_extension(content)}"
            (folder / name).write_bytes(content)


def is_basemap(data_id: str) -> bool:
    return Path(geode_functions.data_file_path(data_id, TILES_FOLDER)).is_dir()

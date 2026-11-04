from __future__ import annotations

# Standard library imports
import io
from dataclasses import dataclass
from typing import TYPE_CHECKING

# Third party imports
from PIL import Image, ImageDraw

# Local application imports
from opengeodeweb_back.basemap.basemap_providers import TILE_SIZE

if TYPE_CHECKING:
    from collections.abc import Iterator

# Mapbox Vector Tile protobuf fields, see https://github.com/mapbox/vector-tile-spec
_TILE_LAYER = 3
_LAYER_NAME, _LAYER_FEATURE, _LAYER_KEY, _LAYER_VALUE, _LAYER_EXTENT = 1, 2, 3, 4, 5
_FEATURE_TAGS, _FEATURE_TYPE, _FEATURE_GEOMETRY = 2, 3, 4
_VALUE_STRING = 1
_LINESTRING = 2
_MOVE_TO, _LINE_TO, _CLOSE_PATH = 1, 2, 7
_VARINT, _FIXED64, _LENGTH, _FIXED32 = 0, 1, 2, 5
# A varint byte below it is the last of its number
_VARINT_CONTINUES = 0x80
DECODE_ERRORS = (IndexError, ValueError, UnicodeDecodeError)

# OpenMapTiles schema: roads are the lines of the transportation layer
ROADS_LAYER = "transportation"
# From the top down: (fill colour, width in pixels at WIDTH_ZOOM)
ROAD_STYLES: dict[str, tuple[tuple[int, int, int], float]] = {
    "motorway": ((233, 144, 160), 3.0),
    "trunk": ((249, 178, 156), 2.6),
    "primary": ((252, 214, 164), 2.2),
    "secondary": ((247, 250, 191), 1.8),
    "tertiary": ((255, 255, 255), 1.4),
    "minor": ((255, 255, 255), 1.0),
    "service": ((255, 255, 255), 0.6),
}
CASING_COLOUR = (90, 90, 90, 255)
CASING_PIXELS = 1.0
MIN_WIDTH_PIXELS = 0.5
WIDTH_ZOOM = 14
# Roads widen less than the ground: a street stays readable without flooding the map
WIDTH_GROWTH_PER_ZOOM = 1.6
# Drawn larger then reduced: Pillow lines are not antialiased
SUPERSAMPLING = 2
# Lines leaving a tile are kept a little: their width still shows past its edge
CLIP_MARGIN = 0.1

type Point = tuple[int, int]


@dataclass(frozen=True)
class Road:
    style: str
    lines: list[list[Point]]
    box: tuple[int, int, int, int]


@dataclass(frozen=True)
class Roads:
    extent: int
    roads: list[Road]


def _varint(buffer: bytes, index: int) -> tuple[int, int]:
    result = shift = 0
    while True:
        byte = buffer[index]
        index += 1
        result |= (byte & 0x7F) << shift
        if byte < _VARINT_CONTINUES:
            return result, index
        shift += 7


def _fields(buffer: bytes) -> Iterator[tuple[int, int | bytes]]:
    index = 0
    while index < len(buffer):
        key, index = _varint(buffer, index)
        wire = key & 7
        value: int | bytes
        if wire == _VARINT:
            value, index = _varint(buffer, index)
        elif wire == _LENGTH:
            length, index = _varint(buffer, index)
            value = buffer[index : index + length]
            index += length
        elif wire in (_FIXED64, _FIXED32):
            size = 8 if wire == _FIXED64 else 4
            value = buffer[index : index + size]
            index += size
        else:
            message = f"Unknown protobuf wire type {wire}"
            raise ValueError(message)
        yield key >> 3, value


def _packed(buffer: bytes) -> list[int]:
    values = []
    index = 0
    while index < len(buffer):
        value, index = _varint(buffer, index)
        values.append(value)
    return values


def _zigzag(value: int) -> int:
    return (value >> 1) ^ -(value & 1)


def _lines(geometry: bytes) -> list[list[Point]]:
    commands = _packed(geometry)
    x = y = index = 0
    lines: list[list[Point]] = []
    current: list[Point] = []
    while index < len(commands):
        command, count = commands[index] & 7, commands[index] >> 3
        index += 1
        if command == _CLOSE_PATH:
            continue
        for _ in range(count):
            # Each point is relative to the previous one
            x += _zigzag(commands[index])
            y += _zigzag(commands[index + 1])
            index += 2
            if command == _MOVE_TO:
                if len(current) > 1:
                    lines.append(current)
                current = [(x, y)]
            elif command == _LINE_TO:
                current.append((x, y))
    if len(current) > 1:
        lines.append(current)
    return lines


def _string(value: bytes) -> str | None:
    for number, field in _fields(value):
        if number == _VALUE_STRING and isinstance(field, bytes):
            return field.decode()
    return None


def _layer_name(layer: bytes) -> str | None:
    for number, field in _fields(layer):
        if number == _LAYER_NAME and isinstance(field, bytes):
            return field.decode()
    return None


def _road(
    feature: bytes, keys: list[str], values: list[str | None]
) -> tuple[dict[str, str | None], list[list[Point]]] | None:
    tags: list[int] = []
    geometry = b""
    kind = 0
    for number, field in _fields(feature):
        if number == _FEATURE_TAGS and isinstance(field, bytes):
            tags = _packed(field)
        elif number == _FEATURE_TYPE and isinstance(field, int):
            kind = field
        elif number == _FEATURE_GEOMETRY and isinstance(field, bytes):
            geometry = field
    if kind != _LINESTRING:
        return None
    properties = {keys[tags[i]]: values[tags[i + 1]] for i in range(0, len(tags) - 1, 2)}
    return properties, _lines(geometry)


def _roads_layer(layer: bytes) -> Roads:
    keys: list[str] = []
    values: list[str | None] = []
    features: list[bytes] = []
    extent = 4096
    for number, field in _fields(layer):
        if number == _LAYER_KEY and isinstance(field, bytes):
            keys.append(field.decode())
        elif number == _LAYER_VALUE and isinstance(field, bytes):
            values.append(_string(field))
        elif number == _LAYER_FEATURE and isinstance(field, bytes):
            features.append(field)
        elif number == _LAYER_EXTENT and isinstance(field, int):
            extent = field
    roads = []
    for feature in features:
        road = _road(feature, keys, values)
        if road is None:
            continue
        properties, lines = road
        style = properties.get("class")
        # Tunnels are underground: they would cross buildings and rivers on the map
        if style not in ROAD_STYLES or properties.get("brunnel") == "tunnel" or not lines:
            continue
        xs = [x for line in lines for x, _ in line]
        ys = [y for line in lines for _, y in line]
        roads.append(Road(style, lines, (min(xs), min(ys), max(xs), max(ys))))
    return Roads(extent, roads)


def decode_roads(content: bytes) -> Roads | None:
    """The roads of a vector tile, or None if it cannot be read."""
    try:
        for number, field in _fields(content):
            # Other layers are skipped whole: buildings make most of a city tile
            if (
                number == _TILE_LAYER
                and isinstance(field, bytes)
                and _layer_name(field) == ROADS_LAYER
            ):
                return _roads_layer(field)
    except DECODE_ERRORS:
        return None
    return Roads(4096, [])


def draw_roads(roads: Roads, depth: int, x: int, y: int, z: int) -> bytes:
    """Transparent PNG of tile (x, y) at zoom z, drawn from roads `depth` zooms above."""
    side = roads.extent / (1 << depth)
    left = (x % (1 << depth)) * side
    top = (y % (1 << depth)) * side
    margin = side * CLIP_MARGIN
    scale = TILE_SIZE * SUPERSAMPLING / side
    growth = WIDTH_GROWTH_PER_ZOOM ** (z - WIDTH_ZOOM)
    visible = [
        road
        for road in roads.roads
        if road.box[2] >= left - margin
        and road.box[0] <= left + side + margin
        and road.box[3] >= top - margin
        and road.box[1] <= top + side + margin
    ]
    image = Image.new("RGBA", (TILE_SIZE * SUPERSAMPLING, TILE_SIZE * SUPERSAMPLING))
    draw = ImageDraw.Draw(image)
    # Every casing first: crossings join instead of being cut by a grey border
    for casing in (True, False):
        for style in reversed(ROAD_STYLES):
            colour, width = ROAD_STYLES[style]
            pixels = max(MIN_WIDTH_PIXELS, width * growth)
            if casing:
                pixels += 2 * CASING_PIXELS
            line_width = max(1, round(pixels * SUPERSAMPLING))
            fill = CASING_COLOUR if casing else (*colour, 255)
            for road in visible:
                if road.style != style:
                    continue
                for line in road.lines:
                    points = [((px - left) * scale, (py - top) * scale) for px, py in line]
                    draw.line(points, fill=fill, width=line_width, joint="curve")
    output = io.BytesIO()
    image.resize((TILE_SIZE, TILE_SIZE), Image.Resampling.LANCZOS).save(output, format="PNG")
    return output.getvalue()

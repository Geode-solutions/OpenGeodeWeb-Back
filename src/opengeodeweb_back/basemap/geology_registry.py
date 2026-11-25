from __future__ import annotations

# Standard library imports
import json
import re
from pathlib import Path
from typing import Any

# Third party imports
import opengeode_geosciences as og_geosciences

# Local application imports
from opengeodeweb_back.basemap.basemap_providers import Source
from opengeodeweb_back.crs.crs_functions import convert_xy_corners

REGISTRY_PATH = Path(__file__).parent / "geology_sources.json"
ID_PREFIX = "geology_"
PROTOCOLS = ("wmts", "xyz", "wms")
COLOUR = re.compile(r"#[0-9a-f]{6}")
# Web Mercator stops short of the poles
MAX_LATITUDE = 85.05
REQUIRED = (
    "id",
    "name",
    "protocol",
    "url",
    "attribution",
    "status",
    "min_scale",
    "max_scale",
    "source_scale",
)
WGS84 = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "4326", "WGS 84")
WEB_MERCATOR = og_geosciences.GeographicCoordinateSystemInfo(
    "EPSG", "3857", "WGS 84 / Pseudo-Mercator"
)


class RegistryError(ValueError):
    pass


def _area_3857(area: list[float] | None) -> tuple[float, float, float, float] | None:
    if area is None:
        return None
    lon_min, lat_min, lon_max, lat_max = area
    clamped = (
        lon_min,
        max(lat_min, -MAX_LATITUDE),
        lon_max,
        min(lat_max, MAX_LATITUDE),
    )
    corners = convert_xy_corners(clamped, WGS84, WEB_MERCATOR)
    xs = [x for x, _ in corners]
    ys = [y for _, y in corners]
    return (min(xs), min(ys), max(xs), max(ys))


def _check(entry: dict[str, Any]) -> None:
    name = entry.get("id", "?")
    missing = [key for key in REQUIRED if entry.get(key) is None]
    if missing:
        msg = f"Geology source {name}: missing {', '.join(missing)}"
        raise RegistryError(msg)
    if not str(name).startswith(ID_PREFIX):
        msg = f"Geology source {name}: the id must start with {ID_PREFIX}"
        raise RegistryError(msg)
    if entry["protocol"] not in PROTOCOLS:
        msg = f"Geology source {name}: unknown protocol {entry['protocol']}"
        raise RegistryError(msg)
    empty_tile = entry.get("empty_tile", "404")
    if empty_tile not in ("404", "transparent") and not COLOUR.fullmatch(empty_tile):
        msg = f"Geology source {name}: empty_tile must be 404, transparent or #rrggbb"
        raise RegistryError(msg)
    if entry["min_scale"] >= entry["max_scale"]:
        msg = f"Geology source {name}: min_scale must be below max_scale"
        raise RegistryError(msg)


def _source(entry: dict[str, Any]) -> Source:
    return Source(
        url_template=entry["url"],
        max_zoom=entry.get("max_zoom") or 0,
        attribution=entry["attribution"],
        min_scale=entry["min_scale"],
        max_scale=entry["max_scale"],
        source_scale=entry["source_scale"],
        area_3857=_area_3857(entry.get("area")),
        empty_tile=entry.get("empty_tile", "404"),
    )


def load(path: Path = REGISTRY_PATH) -> dict[str, Source]:
    """The verified geology sources by id, the most detailed first."""
    entries: list[dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    seen: set[str] = set()
    for entry in entries:
        _check(entry)
        if entry["id"] in seen:
            msg = f"Geology source {entry['id']}: duplicate id"
            raise RegistryError(msg)
        seen.add(entry["id"])
    verified = [entry for entry in entries if entry["status"] == "verified"]
    # Stable: sources of the same scale keep the registry order
    verified.sort(key=lambda entry: entry["source_scale"])
    return {entry["id"]: _source(entry) for entry in verified}

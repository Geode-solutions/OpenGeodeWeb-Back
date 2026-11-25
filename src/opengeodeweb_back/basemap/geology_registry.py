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
PROTOCOLS = ("wmts", "xyz", "wms", "export")
COLOUR = re.compile(r"#[0-9a-f]{6}")
# Web Mercator first: its tiles fall on the tile grid. Else longitude first, then latitude first
WMS_CRS_PREFERENCE = ("EPSG:3857", "CRS:84", "EPSG:4326")
# No tile grid caps a WMS: past this zoom its tiles are enlarged
WMS_MAX_ZOOM = 18
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
    # A WMS without a usable CRS or an export without {bbox} is rejected, even unverified
    _url(entry)


def _wms(entry: dict[str, Any]) -> tuple[str, str]:
    """The GetMap template of a WMS entry, with its {bbox}, and the CRS it asks."""
    supported = entry.get("supported_crs") or []
    crs = next((crs for crs in WMS_CRS_PREFERENCE if crs in supported), None)
    if crs is None:
        msg = (
            f"Geology source {entry['id']}: the WMS serves none of {', '.join(WMS_CRS_PREFERENCE)}"
        )
        raise RegistryError(msg)
    query = (
        "SERVICE=WMS&VERSION=1.3.0&REQUEST=GetMap"
        f"&LAYERS={entry['layers']}&STYLES={entry.get('styles') or ''}&CRS={crs}"
        "&BBOX={bbox}&WIDTH=256&HEIGHT=256"
        f"&FORMAT={entry['format']}&TRANSPARENT=TRUE"
    )
    separator = "&" if "?" in entry["url"] else "?"
    return f"{entry['url']}{separator}{query}", crs


def _url(entry: dict[str, Any]) -> tuple[str, str | None]:
    """The tile URL template of an entry, and the CRS of its {bbox} when it has one."""
    if entry["protocol"] == "wms":
        return _wms(entry)
    if entry["protocol"] == "export":
        # A map server export: a full template, asked in Web Mercator
        if "{bbox}" not in entry["url"]:
            msg = f"Geology source {entry['id']}: an export url needs a {{bbox}}"
            raise RegistryError(msg)
        return entry["url"], "EPSG:3857"
    return entry["url"], None


def _source(entry: dict[str, Any]) -> Source:
    url_template, wms_crs = _url(entry)
    bbox_protocol = entry["protocol"] in ("wms", "export")
    return Source(
        url_template=url_template,
        max_zoom=entry.get("max_zoom") or (WMS_MAX_ZOOM if bbox_protocol else 0),
        attribution=entry["attribution"],
        min_scale=entry["min_scale"],
        max_scale=entry["max_scale"],
        source_scale=entry["source_scale"],
        area_3857=_area_3857(entry.get("area")),
        empty_tile=entry.get("empty_tile", "404"),
        wms_crs=wms_crs,
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

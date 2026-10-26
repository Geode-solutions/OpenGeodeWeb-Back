from __future__ import annotations

# Standard library imports
import os
from dataclasses import dataclass


@dataclass(frozen=True)
class StyleInfo:
    default_url: str
    tile_size: int
    attribution: str


class MissingApiKeyError(Exception):
    pass


_STATIC_TILES = (
    "https://static-map-tiles-api.arcgis.com/arcgis/rest/services/"
    "static-basemap-tiles-service/v1/arcgis/{style}/static/tile/{{z}}/{{y}}/{{x}}?token={{token}}"
)
_ESRI_DATA = "Esri, HERE, Garmin, FAO, NOAA, USGS, © OpenStreetMap contributors"

STYLES: dict[str, StyleInfo] = {
    "satellite": StyleInfo(
        "https://ibasemaps-api.arcgis.com/arcgis/rest/services/World_Imagery/MapServer/tile/"
        "{z}/{y}/{x}?token={token}",
        256,
        "Powered by Esri | Esri, Maxar, Earthstar Geographics, and the GIS User Community",
    ),
    "streets": StyleInfo(
        _STATIC_TILES.format(style="streets"), 512, f"Powered by Esri | {_ESRI_DATA}"
    ),
    "topo": StyleInfo(
        _STATIC_TILES.format(style="outdoor"), 512, f"Powered by Esri | {_ESRI_DATA}"
    ),
}


def _url_template(style: str) -> str:
    return os.environ.get(f"BASEMAP_TILE_URL_{style.upper()}", STYLES[style].default_url)


def tile_url(style: str, z: int, x: int, y: int) -> str:
    template = _url_template(style)
    token = ""
    if "{token}" in template:
        token = os.environ.get("ARCGIS_API_KEY", "")
        if not token:
            msg = "Basemap unavailable: no API key"
            raise MissingApiKeyError(msg)
    return template.format(z=z, x=x, y=y, token=token)


def attribution(style: str) -> str:
    return STYLES[style].attribution

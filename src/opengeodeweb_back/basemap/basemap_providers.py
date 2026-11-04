from __future__ import annotations

# Standard library imports
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

USER_AGENT = "Vease (+https://geode-solutions.com)"
# Every source is cut in 256 px Web Mercator tiles: they share one tile grid
TILE_SIZE = 256


@dataclass(frozen=True)
class Source:
    url_template: str
    max_zoom: int
    attribution: str


_GEOPLATEFORME = (
    "https://data.geopf.fr/wmts?SERVICE=WMTS&REQUEST=GetTile&VERSION=1.0.0&LAYER={layer}"
    "&STYLE=normal&TILEMATRIXSET=PM&TILEMATRIX={{z}}&TILEROW={{y}}&TILECOL={{x}}&FORMAT={format}"
)
_IGN = "© IGN"

SOURCES: dict[str, Source] = {
    "eox_s2cloudless_2016": Source(
        "https://tiles.maps.eox.at/wmts/1.0.0/s2cloudless_3857/default/g/{z}/{y}/{x}.jpg",
        17,
        "Sentinel-2 cloudless 2016 by EOX IT Services GmbH "
        "(Contains modified Copernicus Sentinel data 2016)",
    ),
    "ign_orthophotos": Source(
        _GEOPLATEFORME.format(layer="ORTHOIMAGERY.ORTHOPHOTOS", format="image/jpeg"), 19, _IGN
    ),
    # Volunteer servers: to be replaced before production, see the basemap design
    "osm": Source(
        "https://tile.openstreetmap.org/{z}/{x}/{y}.png", 19, "© OpenStreetMap contributors"
    ),
    "ign_plan": Source(
        _GEOPLATEFORME.format(layer="GEOGRAPHICALGRIDSYSTEMS.PLANIGNV2", format="image/png"),
        19,
        _IGN,
    ),
    "ign_roads": Source(
        _GEOPLATEFORME.format(layer="TRANSPORTNETWORKS.ROADS", format="image/png"), 18, _IGN
    ),
    "eox_overlay": Source(
        "https://tiles.maps.eox.at/wmts/1.0.0/overlay_3857/default/g/{z}/{y}/{x}.png",
        14,
        "© OpenStreetMap contributors, rendering © EOX",
    ),
}

# From the bottom up: in a map, the IGN covers the world source where it has tiles (France)
MAPS: dict[str, tuple[str, ...]] = {
    "satellite": ("eox_s2cloudless_2016", "ign_orthophotos"),
    "plan": ("osm", "ign_plan"),
    "routes": ("ign_roads", "eox_overlay"),
}


def url_template(source: str) -> str:
    return os.environ.get(f"BASEMAP_TILE_URL_{source.upper()}", SOURCES[source].url_template)


def sorted_maps(maps: Iterable[str]) -> list[str]:
    requested = set(maps)
    return [name for name in MAPS if name in requested]


def map_layers(maps: list[str], served: Callable[[str], bool]) -> dict[str, list[str]]:
    """The sources drawn by each sorted map, from the bottom up: maps without any are left out."""
    layers: dict[str, list[str]] = {}
    for name in maps:
        sources = [source for source in MAPS[name] if served(source)]
        # Transparent routes: both sources would draw the same roads, the first served wins
        if name == "routes":
            sources = sources[:1]
        if sources:
            layers[name] = sources
    return layers


def max_zoom(sources: Iterable[str]) -> int:
    # The grid follows the finest source: coarser ones are overzoomed
    return max(SOURCES[source].max_zoom for source in sources)


def attribution(sources: Iterable[str]) -> str:
    return " | ".join(dict.fromkeys(SOURCES[source].attribution for source in sources))

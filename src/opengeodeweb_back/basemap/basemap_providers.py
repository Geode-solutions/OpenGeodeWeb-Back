from __future__ import annotations

# Standard library imports
import math
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Container, Iterable

USER_AGENT = "Vease (+https://geode-solutions.com)"
# Every source is cut in 256 px Web Mercator tiles: they share one tile grid
TILE_SIZE = 256


@dataclass(frozen=True)
class Source:
    url_template: str
    max_zoom: int
    attribution: str
    # A tile-by-tile layer asks a source only for the tiles of its scale window (in scale
    # denominators) and of its Web Mercator area (None for the whole world)
    min_scale: float = 0.0
    max_scale: float = math.inf
    area_3857: tuple[float, float, float, float] | None = None
    # Scale of the data, None when unknown
    source_scale: float | None = None
    # How the server says it has no data: a 404, a transparent tile or a plain colour tile
    empty_tile: str = "404"
    # Sources asked by bounding box (WMS, map server export): the CRS of their {bbox}
    bbox_crs: str | None = None


@dataclass(frozen=True)
class Layer:
    """The sources of one layer of a map, the preferred first."""

    sources: tuple[str, ...]
    # False: the first source serving any tile draws the whole layer, one style per mosaic.
    # True: each tile takes the first source whose scale window and area hold it and that serves it
    tile_by_tile: bool = False


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


def _geology_sources() -> dict[str, Source]:
    # Imported here: the registry builds Source objects of this module
    from opengeodeweb_back.basemap import geology_registry  # noqa: PLC0415

    return geology_registry.load()


_GEOLOGY = _geology_sources()
SOURCES.update(_GEOLOGY)
# The geology sources, the most detailed first
GEOLOGY_SOURCES: tuple[str, ...] = tuple(_GEOLOGY)

# The layers of each map, from the bottom up
MAPS: dict[str, tuple[Layer, ...]] = {
    # The IGN covers the world imagery or map where it has tiles (France)
    "satellite": (Layer(("eox_s2cloudless_2016",)), Layer(("ign_orthophotos",))),
    "plan": (Layer(("osm",)), Layer(("ign_plan",))),
    # Under the roads, which stay readable over it. Each survey fills the tiles it serves
    "geology": (Layer(GEOLOGY_SOURCES, tile_by_tile=True),),
    # Transparent: both sources would draw the same roads twice, EOX outside France
    "routes": (Layer(("ign_roads", "eox_overlay")),),
}


def url_template(source: str) -> str:
    # Local servers for tests: one variable per source, else one for all where {source} is replaced
    template = os.environ.get(f"BASEMAP_TILE_URL_{source.upper()}")
    if template is not None:
        return template
    shared = os.environ.get("BASEMAP_TILE_URL")
    if shared is not None:
        return shared.replace("{source}", source)
    return SOURCES[source].url_template


def sorted_maps(maps: Iterable[str]) -> list[str]:
    requested = set(maps)
    return [name for name in MAPS if name in requested]


def map_layers(maps: list[str], served: Container[str]) -> dict[str, list[str]]:
    """The served sources of each sorted map, from the bottom up: maps without any are left out."""
    layers = {
        name: [source for layer in MAPS[name] for source in layer.sources if source in served]
        for name in maps
    }
    return {name: sources for name, sources in layers.items() if sources}


def max_zoom(sources: Iterable[str]) -> int:
    # The grid follows the finest source: coarser ones are overzoomed
    return max(SOURCES[source].max_zoom for source in sources)


def attribution(sources: Iterable[str]) -> str:
    return " | ".join(dict.fromkeys(SOURCES[source].attribution for source in sources))

from __future__ import annotations

# Standard library imports
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third party imports
import flask
from opengeodeweb_microservice.database.connection import get_session

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.basemap import basemap_mesh, basemap_providers, basemap_tiles
from opengeodeweb_back.crs.crs_functions import geographic_coordinate_systems
from opengeodeweb_back.routes.basemap import schemas
from opengeodeweb_back.typed_route import typed_route

if TYPE_CHECKING:
    import opengeode_geosciences as og_geosciences

    from opengeodeweb_back.geode_objects.geode_triangulated_surface3d import (
        GeodeTriangulatedSurface3D,
    )

routes = flask.Blueprint("basemap", __name__, url_prefix="/basemap")
logger = logging.getLogger(__name__)

MARGIN_RATIO = 0.5
MIN_SIZE = 1_000.0  # metres, in Web Mercator

Images = dict[str, dict[tuple[int, int], bytes | None]]


def padded(bounds: tuple[float, float, float, float]) -> tuple[float, float, float, float]:
    # Web Mercator bounds: units are metres whatever the project CRS
    x_min, y_min, x_max, y_max = bounds
    half_width = max(x_max - x_min, MIN_SIZE) * (0.5 + MARGIN_RATIO)
    half_height = max(y_max - y_min, MIN_SIZE) * (0.5 + MARGIN_RATIO)
    center_x = (x_min + x_max) / 2
    center_y = (y_min + y_max) / 2
    return (
        center_x - half_width,
        center_y - half_height,
        center_x + half_width,
        center_y + half_height,
    )


def _crs(params: schemas.CRSParams) -> og_geosciences.GeographicCoordinateSystemInfo:
    key = f"{params.authority}:{params.code}"
    # The basemap is a 3D mesh: only list the CRS a 3D object accepts
    crs = geographic_coordinate_systems(True).get(key)  # noqa: FBT003
    if crs is None:
        flask.abort(400, f"Unknown CRS {key}")
    return crs


def _tile_range(
    params: schemas.Build,
    crs: og_geosciences.GeographicCoordinateSystemInfo,
    sources: list[str],
) -> basemap_tiles.TileRange:
    raw = (params.bounds.x_min, params.bounds.y_min, params.bounds.x_max, params.bounds.y_max)
    projected = basemap_mesh.bounds_to_3857(raw, crs)
    # The margin is on unless asked off: a detail covers the visible area only
    with_margin = params.margin is None or params.margin
    # One tile grid for every source: the viewer stacks their mosaics pixel on pixel
    return basemap_tiles.tile_range(
        padded(projected) if with_margin else projected,
        basemap_providers.max_zoom(sources),
        params.max_pixels or basemap_tiles.DEFAULT_MAX_PIXELS,
    )


def _save_tiles(data_id: str, tiles: basemap_tiles.TileRange, images: Images) -> None:
    data_folder = Path(geode_functions.data_file_path(data_id))
    try:
        for source, source_images in images.items():
            basemap_tiles.save_tiles(
                tiles, source_images, data_folder / basemap_tiles.TILES_FOLDER / source
            )
    except OSError:
        # The request rolls the data row back: its folder must not stay behind
        shutil.rmtree(data_folder, ignore_errors=True)
        raise


def _mesh_bounds(mesh: GeodeTriangulatedSurface3D) -> dict[str, float]:
    box = mesh.triangulated_surface.bounding_box()
    return {
        "x_min": box.min().value(0),
        "y_min": box.min().value(1),
        "x_max": box.max().value(0),
        "y_max": box.max().value(1),
    }


@typed_route(routes, schemas.build_route)
def build(params: schemas.Build) -> schemas.BuildResponse:
    crs = _crs(params.crs)
    maps = basemap_providers.sorted_maps(map_.value for map_ in params.maps)
    fetched = [layer for name in maps for layer in basemap_providers.MAPS[name]]
    try:
        tiles = _tile_range(params, crs, [source for layer in fetched for source in layer])
        images = basemap_tiles.fetch_layers(fetched, tiles)
        # Outside France the IGN sources have no tile: the others still make the map
        layers = basemap_providers.map_layers(maps, images)
        drawn = [source for names in layers.values() for source in names]
        if not drawn:
            logger.warning("No basemap tile downloaded (maps %s, zoom %d)", maps, tiles.z)
            flask.abort(502, "Basemap unavailable: no tile could be downloaded")
        mesh = basemap_mesh.build_mesh(tiles, crs, params.z)
    except basemap_mesh.OutsideProjectionError as error:
        flask.abort(400, str(error))
    response: dict[str, Any] = utils_functions.generate_files_from_object(mesh)
    _save_tiles(response["id"], tiles, {source: images[source] for source in drawn})
    response["columns"] = tiles.x_max - tiles.x_min + 1
    response["rows"] = tiles.y_max - tiles.y_min + 1
    response["maps"] = [{"map": name, "sources": names} for name, names in layers.items()]
    response["attribution"] = basemap_providers.attribution(drawn)
    response["zoom"] = tiles.z
    response["bounds"] = _mesh_bounds(mesh)
    return schemas.BuildResponse.from_dict(response)


@typed_route(routes, schemas.delete_route)
def delete(params: schemas.Delete) -> schemas.DeleteResponse:
    data = geode_functions.get_data_info(params.id)
    # No other data can be deleted here
    if not basemap_tiles.is_basemap(params.id):
        flask.abort(400, f"Data {params.id} is not a basemap")
    get_session().delete(data)
    shutil.rmtree(geode_functions.data_file_path(params.id))
    return schemas.DeleteResponse(id=params.id)

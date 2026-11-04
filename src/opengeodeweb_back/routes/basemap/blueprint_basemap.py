from __future__ import annotations

# Standard library imports
import logging
import shutil
from pathlib import Path
from typing import Any

# Third party imports
import flask
from opengeodeweb_microservice.database.connection import get_session

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.basemap import basemap_mesh, basemap_providers, basemap_tiles
from opengeodeweb_back.crs.crs_functions import geographic_coordinate_systems
from opengeodeweb_back.routes.basemap import schemas
from opengeodeweb_back.typed_route import typed_route

routes = flask.Blueprint("basemap", __name__, url_prefix="/basemap")
logger = logging.getLogger(__name__)

MARGIN_RATIO = 0.5
MIN_SIZE = 1_000.0  # metres, in Web Mercator


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


@typed_route(routes, schemas.build_route)
def build(params: schemas.Build) -> schemas.BuildResponse:
    # The basemap is a 3D mesh: only list the CRS a 3D object accepts
    crs = geographic_coordinate_systems(True).get(f"{params.crs.authority}:{params.crs.code}")  # noqa: FBT003
    if crs is None:
        flask.abort(400, f"Unknown CRS {params.crs.authority}:{params.crs.code}")
    maps = basemap_providers.sorted_maps(map_.value for map_ in params.maps)
    fetched = [layer for name in maps for layer in basemap_providers.MAPS[name]]
    sources = [source for layer in fetched for source in layer]
    try:
        raw = (params.bounds.x_min, params.bounds.y_min, params.bounds.x_max, params.bounds.y_max)
        projected = basemap_mesh.bounds_to_3857(raw, crs)
        # A detail covers the visible area only: no margin around it
        bounds = padded(projected) if params.margin is not False else projected
        # One tile grid for every source: the viewer stacks their mosaics pixel on pixel
        tiles = basemap_tiles.tile_range(
            bounds,
            basemap_providers.max_zoom(sources),
            params.max_pixels or basemap_tiles.DEFAULT_MAX_PIXELS,
        )
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
    box = mesh.triangulated_surface.bounding_box()
    response: dict[str, Any] = utils_functions.generate_files_from_object(mesh)
    data_folder = Path(geode_functions.data_file_path(response["id"]))
    try:
        for source in drawn:
            basemap_tiles.save_tiles(
                tiles, images[source], data_folder / basemap_tiles.TILES_FOLDER / source
            )
    except OSError:
        # The request rolls the data row back: its folder must not stay behind
        shutil.rmtree(data_folder, ignore_errors=True)
        raise
    response["columns"] = tiles.x_max - tiles.x_min + 1
    response["rows"] = tiles.y_max - tiles.y_min + 1
    response["maps"] = [{"map": name, "sources": names} for name, names in layers.items()]
    response["attribution"] = basemap_providers.attribution(drawn)
    response["zoom"] = tiles.z
    response["bounds"] = {
        "x_min": box.min().value(0),
        "y_min": box.min().value(1),
        "x_max": box.max().value(0),
        "y_max": box.max().value(1),
    }
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

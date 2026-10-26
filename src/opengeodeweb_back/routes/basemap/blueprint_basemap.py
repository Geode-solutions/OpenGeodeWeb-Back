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
from opengeodeweb_back.crs_functions import geographic_coordinate_systems
from opengeodeweb_back.routes.basemap import schemas
from opengeodeweb_back.typed_route import typed_route

routes = flask.Blueprint("basemap", __name__, url_prefix="/basemap")
logger = logging.getLogger(__name__)

MARGIN_RATIO = 0.5
MIN_SIZE = 1_000.0  # metres, in Web Mercator
TILES_FOLDER = "tiles"


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
    style = params.style.value
    try:
        raw = (params.bounds.x_min, params.bounds.y_min, params.bounds.x_max, params.bounds.y_max)
        bounds = padded(basemap_mesh.bounds_to_3857(raw, crs))
        tiles = basemap_tiles.tile_range(bounds, basemap_providers.STYLES[style].tile_size)
        images = basemap_tiles.fetch_tiles(style, tiles)
        if not any(images.values()):
            # Never log the URL: it holds the API key
            logger.warning("No basemap tile downloaded (style %s, zoom %d)", style, tiles.z)
            flask.abort(502, "Basemap unavailable: no tile could be downloaded")
        mesh = basemap_mesh.build_mesh(tiles, crs, params.z, "basemap")
    except (basemap_providers.MissingApiKeyError, basemap_mesh.OutsideProjectionError) as error:
        flask.abort(400, str(error))
    response: dict[str, Any] = utils_functions.generate_files_from_object(mesh)
    basemap_tiles.save_tiles(
        tiles, images, Path(geode_functions.data_file_path(response["id"], TILES_FOLDER))
    )
    response["tiles_folder"] = TILES_FOLDER
    response["columns"] = tiles.x_max - tiles.x_min + 1
    response["rows"] = tiles.y_max - tiles.y_min + 1
    response["attribution"] = basemap_providers.attribution(style)
    return schemas.BuildResponse.from_dict(response)


@typed_route(routes, schemas.delete_route)
def delete(params: schemas.Delete) -> schemas.DeleteResponse:
    data = geode_functions.get_data_info(params.id)
    folder = Path(geode_functions.data_file_path(params.id))
    # Only basemaps have a tiles folder: no other data can be deleted here
    if not (folder / TILES_FOLDER).is_dir():
        flask.abort(400, f"Data {params.id} is not a basemap")
    get_session().delete(data)
    shutil.rmtree(folder)
    return schemas.DeleteResponse(id=params.id)

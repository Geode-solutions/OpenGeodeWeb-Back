# Standard library imports
from typing import Any

# Third party imports
import flask
import opengeode as og
import opengeode_geosciences as og_geosciences

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.crs_functions import (
    CRS_GEODE_OBJECTS,
    CrsGeodeObject,
    geographic_info,
)
from opengeodeweb_back.routes.crs import schemas
from opengeodeweb_back.typed_route import typed_route

routes = flask.Blueprint("crs", __name__, url_prefix="/crs")


def _prepare_crs_name(
    geode_object: CrsGeodeObject,
    crs_name: str,
) -> None:
    crs_manager = geode_object.crs_manager()
    info = geographic_info(crs_manager)
    if info is not None and info.authority_code() == crs_name:
        flask.abort(400, f"{crs_name} is already the active CRS")
    # A registered inactive CRS may hold coordinates derived from an outdated label: recompute it
    if crs_manager.coordinate_reference_system_exists(crs_name):
        geode_object.delete_crs(crs_name)


def _crs_response(saved: dict[str, Any]) -> dict[str, Any]:
    # Only the fields the front refreshes after a CRS change
    return {key: saved[key] for key in ("crs", "binary_light_viewable") if key in saved}


@typed_route(routes, schemas.geographic_list_route)
def geographic_list(params: schemas.GeographicList) -> schemas.GeographicListResponse:
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type)
    infos = (
        og_geosciences.GeographicCoordinateSystem3D.geographic_coordinate_systems()
        if geode_object.is_3d()
        else og_geosciences.GeographicCoordinateSystem2D.geographic_coordinate_systems()
    )
    crs_list = [
        schemas.geographic_list.CRSList(name=info.name, code=info.code, authority=info.authority)
        for info in infos
    ]
    return schemas.GeographicListResponse(crs_list=crs_list)


@typed_route(routes, schemas.active_route)
def active(params: schemas.Active) -> schemas.ActiveResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    crs_manager = geode_object.crs_manager()
    info = geographic_info(crs_manager)
    crs_info = (
        None
        if info is None
        else schemas.active.CRSInfo(authority=info.authority, code=info.code, name=info.name)
    )
    return schemas.ActiveResponse(
        crs_name=crs_manager.active_coordinate_reference_system_name(),
        crs_info=crs_info,
    )


@typed_route(routes, schemas.assign_geographic_route)
def assign_geographic(params: schemas.AssignGeographic) -> schemas.AssignGeographicResponse:
    data = geode_functions.get_data_info(params.id)
    geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
        geode_functions.data_file_path(params.id, data.native_file)
    )
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    info = og_geosciences.GeographicCoordinateSystemInfo(params.authority, params.code, params.name)
    _prepare_crs_name(geode_object, info.authority_code())
    geode_object.assign_crs(info.authority_code(), info)
    saved = utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    return schemas.AssignGeographicResponse.from_dict(_crs_response(saved))


@typed_route(routes, schemas.convert_geographic_route)
def convert_geographic(params: schemas.ConvertGeographic) -> schemas.ConvertGeographicResponse:
    data = geode_functions.get_data_info(params.id)
    geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
        geode_functions.data_file_path(params.id, data.native_file)
    )
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    crs_manager = geode_object.crs_manager()
    if geographic_info(crs_manager) is None:
        flask.abort(400, "Assign a geographic CRS before converting")
    info = og_geosciences.GeographicCoordinateSystemInfo(params.authority, params.code, params.name)
    _prepare_crs_name(geode_object, info.authority_code())
    try:
        geode_object.convert_crs(info.authority_code(), info)
    except RuntimeError:  # PROJ rejects coordinates outside the source or target CRS domain
        flask.abort(400, f"Coordinates cannot be converted to {info.authority_code()}")
    saved = utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    # The front rebuilds its local actor from the new light viewable
    return schemas.ConvertGeographicResponse.from_dict(_crs_response(saved))


def _coordinate_system(
    points: list[schemas.SourcePoint] | list[schemas.TargetPoint],
) -> og.CoordinateSystem2D:
    origin, first, second = (og.Point2D([point.x, point.y]) for point in points)
    return og.CoordinateSystem2D(origin, [first, second])


@typed_route(routes, schemas.align_route)
def align(params: schemas.Align) -> schemas.AlignResponse:
    data = geode_functions.get_data_info(params.id)
    geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
        geode_functions.data_file_path(params.id, data.native_file)
    )
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    if geographic_info(geode_object.crs_manager()) is not None:
        flask.abort(400, "Data already has a geographic CRS, use convert")
    try:
        source = _coordinate_system(params.source_points)
        target = _coordinate_system(params.target_points)
    except RuntimeError:  # OpenGeode cannot build a coordinate system from colinear points
        flask.abort(400, "Points must not be colinear")
    geode_object.create_crs("aligned", source, target)
    info = og_geosciences.GeographicCoordinateSystemInfo(params.authority, params.code, params.name)
    geode_object.assign_crs(info.authority_code(), info)
    saved = utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    # The front rebuilds its local actor from the new light viewable
    return schemas.AlignResponse.from_dict(_crs_response(saved))

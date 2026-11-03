from __future__ import annotations

# Standard library imports
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any

# Third party imports
import flask

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.crs import crs_alignment, crs_assignment
from opengeodeweb_back.crs.crs_functions import (
    CRS_GEODE_OBJECTS,
    CrsError,
    geographic_coordinate_systems,
    geographic_info,
    known_info,
    linked_objects,
    load_crs_object,
)
from opengeodeweb_back.routes.crs import schemas
from opengeodeweb_back.typed_route import typed_route

if TYPE_CHECKING:
    from collections.abc import Generator

    from opengeodeweb_microservice.database.data import Data

    from opengeodeweb_back.crs.crs_functions import CrsGeodeObject

routes = flask.Blueprint("crs", __name__, url_prefix="/crs")


@contextmanager
def _bad_request() -> Generator[None]:
    # The CRS package reports what the data cannot follow: a request error, the data unchanged
    try:
        yield
    except CrsError as error:
        flask.abort(400, str(error))


def _crs_response(saved: dict[str, Any]) -> dict[str, Any]:
    # Only the fields the front refreshes after a CRS change
    return {key: saved[key] for key in ("crs", "binary_light_viewable") if key in saved}


def _saved_response(data_id: str, data: Data, geode_object: CrsGeodeObject) -> dict[str, Any]:
    # The front rebuilds the local actors from the new light viewables
    return _crs_response(
        utils_functions.save_all_viewables_and_return_info(
            geode_object, data, geode_functions.data_file_path(data_id)
        )
    )


@typed_route(routes, schemas.geographic_list_route)
def geographic_list(params: schemas.GeographicList) -> schemas.GeographicListResponse:
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type)
    crs_list = [
        schemas.geographic_list.CRSList(name=info.name, code=info.code, authority=info.authority)
        for info in geographic_coordinate_systems(geode_object.is_3d()).values()
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
    with _bad_request():
        data, geode_object = load_crs_object(params.id)
        linked = linked_objects(params.id, params.linked_ids)
        entries = crs_assignment.assign_all(
            [(params.id, data, geode_object), *linked],
            params.authority,
            params.code,
            only_plausible=bool(params.only_plausible),
        )
    response = entries[params.id]
    if linked:
        response["linked"] = [{"id": linked_id, **entries[linked_id]} for linked_id, _, _ in linked]
    return schemas.AssignGeographicResponse.from_dict(response)


@typed_route(routes, schemas.convert_geographic_route)
def convert_geographic(params: schemas.ConvertGeographic) -> schemas.ConvertGeographicResponse:
    with _bad_request():
        data, geode_object = load_crs_object(params.id)
        linked = linked_objects(params.id, params.linked_ids)
        # Every data is converted in memory before any file is written
        crs_assignment.convert(geode_object, params.authority, params.code)
        for _, _, linked_object in linked:
            crs_assignment.convert(linked_object, params.authority, params.code)
    response = _saved_response(params.id, data, geode_object)
    if linked:
        response["linked"] = [
            {"id": linked_id, **_saved_response(linked_id, linked_data, linked_object)}
            for linked_id, linked_data, linked_object in linked
        ]
    return schemas.ConvertGeographicResponse.from_dict(response)


@typed_route(routes, schemas.align_route)
def align(params: schemas.Align) -> schemas.AlignResponse:
    with _bad_request():
        data, geode_object = load_crs_object(params.id)
        info = known_info(geode_object, params.authority, params.code)
        crs_alignment.check_pair_count(len(params.source_points), len(params.target_points))
        # Linked data share the local frame of the aligned one
        linked = linked_objects(params.id, params.linked_ids)
        source, target = crs_alignment.coordinate_systems(
            crs_alignment.source_points_in_original_coordinates(geode_object, params.source_points),
            crs_alignment.points(params.target_points),
        )
        alignment = crs_alignment.Alignment(source, target, info)
        crs_alignment.apply_alignment(geode_object, alignment)
        for _, _, linked_object in linked:
            crs_alignment.apply_alignment(linked_object, alignment)
    response = _saved_response(params.id, data, geode_object)
    if linked:
        response["linked"] = [
            {"id": linked_id, **_saved_response(linked_id, linked_data, linked_object)}
            for linked_id, linked_data, linked_object in linked
        ]
    return schemas.AlignResponse.from_dict(response)

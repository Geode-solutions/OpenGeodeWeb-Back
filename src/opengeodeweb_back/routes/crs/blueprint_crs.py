from __future__ import annotations

# Standard library imports
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

# Third party imports
import flask
import opengeode as og

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.crs_functions import (
    CRS_GEODE_OBJECTS,
    CRS_GEODE_OBJECTS_3D,
    ORIGINAL_CRS,
    CrsGeodeObject,
    active_crs,
    coordinates_implausible,
    geographic_coordinate_systems,
    geographic_info,
    is_projected,
    known_geographic_info,
    original_coordinates,
)
from opengeodeweb_back.routes.crs import schemas
from opengeodeweb_back.typed_route import typed_route

if TYPE_CHECKING:
    import opengeode_geosciences as og_geosciences
    from opengeodeweb_microservice.database.data import Data

routes = flask.Blueprint("crs", __name__, url_prefix="/crs")

SIMILARITY = "similarity"
AFFINE = "affine"
SIMILARITY_PAIRS = (1, 2)
AFFINE_PAIRS = 3


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


def _known_info(
    geode_object: CrsGeodeObject, authority: str, code: str
) -> og_geosciences.GeographicCoordinateSystemInfo:
    # PROJ crashes the process on an unknown CRS: only accept listed ones, with their own name
    info = known_geographic_info(geode_object, authority, code)
    if info is None:
        flask.abort(400, f"Unknown CRS {authority}:{code}")
    return info


def _crs_response(saved: dict[str, Any]) -> dict[str, Any]:
    # Only the fields the front refreshes after a CRS change
    return {key: saved[key] for key in ("crs", "binary_light_viewable") if key in saved}


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


def _keep_original_coordinates(geode_object: CrsGeodeObject) -> None:
    """Assigning renames the active CRS: assign a copy so "points" survives for re-align."""
    if not all(
        mesh.main_coordinate_reference_system_manager().active_coordinate_reference_system_name()
        == ORIGINAL_CRS
        for mesh in geode_object.crs_meshes()
    ):
        return
    identity = _coordinate_system([og.Point2D([0, 0]), og.Point2D([1, 0]), og.Point2D([0, 1])])
    geode_object.create_crs("assigned", identity, identity)


def _linked_objects(
    data_id: str, linked_ids: list[str] | None
) -> list[tuple[str, Data, CrsGeodeObject]]:
    """Data sharing the change of the main one, all loaded before any file is written."""
    linked_ids = linked_ids or []
    if data_id in linked_ids:
        flask.abort(400, "The data cannot also be linked to itself")
    return [(linked_id, *_load_crs_object(linked_id)) for linked_id in linked_ids]


def _assign(
    geode_object: CrsGeodeObject, authority: str, code: str
) -> og_geosciences.GeographicCoordinateSystemInfo:
    info = _known_info(geode_object, authority, code)
    _prepare_crs_name(geode_object, info.authority_code())
    _keep_original_coordinates(geode_object)
    geode_object.assign_crs(info.authority_code(), info)
    return info


@typed_route(routes, schemas.assign_geographic_route)
def assign_geographic(params: schemas.AssignGeographic) -> schemas.AssignGeographicResponse:
    data, geode_object = _load_crs_object(params.id)
    linked = _linked_objects(params.id, params.linked_ids)
    # Every data is assigned in memory before any file is written
    info = _assign(geode_object, params.authority, params.code)
    linked_infos = [
        _assign(linked_object, params.authority, params.code) for _, _, linked_object in linked
    ]
    # Assigning only relabels the coordinates: the viewables are unchanged
    geode_object.save(geode_functions.data_file_path(params.id, data.native_file))
    for linked_id, linked_data, linked_object in linked:
        linked_object.save(geode_functions.data_file_path(linked_id, linked_data.native_file))
    # A warning only: the label is kept, the front offers to align instead
    response: dict[str, Any] = {
        "crs": active_crs(geode_object),
        "implausible": coordinates_implausible(geode_object, info),
    }
    if linked:
        response["linked"] = [
            {
                "id": linked_id,
                "crs": active_crs(linked_object),
                "implausible": coordinates_implausible(linked_object, linked_info),
            }
            for (linked_id, _, linked_object), linked_info in zip(linked, linked_infos, strict=True)
        ]
    return schemas.AssignGeographicResponse.from_dict(response)


def _convert(geode_object: CrsGeodeObject, authority: str, code: str) -> None:
    if geographic_info(geode_object.crs_manager()) is None:
        flask.abort(400, "Assign a geographic CRS before converting")
    info = _known_info(geode_object, authority, code)
    _prepare_crs_name(geode_object, info.authority_code())
    try:
        geode_object.convert_crs(info.authority_code(), info)
    except RuntimeError:  # PROJ rejects coordinates outside the source or target CRS domain
        flask.abort(400, f"Coordinates cannot be converted to {info.authority_code()}")


@typed_route(routes, schemas.convert_geographic_route)
def convert_geographic(params: schemas.ConvertGeographic) -> schemas.ConvertGeographicResponse:
    data, geode_object = _load_crs_object(params.id)
    linked = _linked_objects(params.id, params.linked_ids)
    # Every data is converted in memory before any file is written
    _convert(geode_object, params.authority, params.code)
    for _, _, linked_object in linked:
        _convert(linked_object, params.authority, params.code)
    saved = utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    # The front rebuilds the local actors from the new light viewables
    response = _crs_response(saved)
    if linked:
        response["linked"] = [
            {
                "id": linked_id,
                **_crs_response(
                    utils_functions.save_all_viewables_and_return_info(
                        linked_object, linked_data, geode_functions.data_file_path(linked_id)
                    )
                ),
            }
            for linked_id, linked_data, linked_object in linked
        ]
    return schemas.ConvertGeographicResponse.from_dict(response)


def _points(
    points: list[schemas.SourcePoint] | list[schemas.TargetPoint],
) -> list[og.Point2D]:
    return [og.Point2D([point.x, point.y]) for point in points]


def _original_source_points(
    geode_object: CrsGeodeObject, source_points: list[schemas.SourcePoint]
) -> list[og.Point2D]:
    """Source points in the loaded coordinates: alignments must not stack.

    Picked points lie on the displayed data: they are mapped back.
    Typed points are already original coordinates.
    """
    points = _points(source_points)
    original_points = original_coordinates(geode_object, points)
    if original_points is None:
        if any(point.picked for point in source_points):
            flask.abort(400, "Data has no three non-colinear vertices to re-align")
        return points
    return [
        original if source.picked else typed
        for source, original, typed in zip(source_points, original_points, points, strict=True)
    ]


def _restart_alignment(geode_object: CrsGeodeObject) -> bool:
    """Go back to the loaded coordinates. True when only the active ones can be aligned."""
    if geographic_info(geode_object.crs_manager()) is None:
        return False
    if not _has_original_coordinates(geode_object):
        return True
    geode_object.set_active_crs(ORIGINAL_CRS)
    _delete_other_crs(geode_object, ORIGINAL_CRS)
    return False


def _crs_names(geode_object: CrsGeodeObject) -> set[str]:
    # Model components may hold different CRS: gather them all
    managers = [
        mesh.main_coordinate_reference_system_manager() for mesh in geode_object.crs_meshes()
    ]
    return {name for manager in managers for name in manager.coordinate_reference_system_names()}


def _has_original_coordinates(geode_object: CrsGeodeObject) -> bool:
    # Assigning a geographic CRS renames the "points" CRS: the assigned coordinates are the base
    return all(
        mesh.main_coordinate_reference_system_manager().coordinate_reference_system_exists(
            ORIGINAL_CRS
        )
        for mesh in geode_object.crs_meshes()
    )


def _delete_other_crs(geode_object: CrsGeodeObject, *kept: str) -> None:
    for crs_name in _crs_names(geode_object):
        if crs_name not in kept:
            geode_object.delete_crs(crs_name)


def _coordinate_system(points: list[og.Point2D]) -> og.CoordinateSystem2D:
    origin, first, second = points
    return og.CoordinateSystem2D(origin, [first, second])


def _frame(origin: og.Point2D, x: float, y: float) -> og.CoordinateSystem2D:
    # Perpendicular axes of equal length: going from one frame to another is a similarity
    return og.CoordinateSystem2D([og.Vector2D([x, y]), og.Vector2D([-y, x])], origin)


def _similarity_coordinate_systems(
    source: list[og.Point2D], target: list[og.Point2D]
) -> tuple[og.CoordinateSystem2D, og.CoordinateSystem2D, float, float]:
    """Frames moving source onto target without distortion, with the scale and rotation."""
    if len(source) == 1:
        return _frame(source[0], 1, 0), _frame(target[0], 1, 0), 1.0, 0.0
    source_x = source[1].value(0) - source[0].value(0)
    source_y = source[1].value(1) - source[0].value(1)
    target_x = target[1].value(0) - target[0].value(0)
    target_y = target[1].value(1) - target[0].value(1)
    source_length = math.hypot(source_x, source_y)
    target_length = math.hypot(target_x, target_y)
    if source_length == 0 or target_length == 0:
        flask.abort(400, "The two points of the source or of the target must differ")
    rotation = math.degrees(
        math.atan2(
            source_x * target_y - source_y * target_x, source_x * target_x + source_y * target_y
        )
    )
    return (
        _frame(source[0], source_x, source_y),
        _frame(target[0], target_x, target_y),
        target_length / source_length,
        rotation,
    )


def _check_pair_count(mode: str, params: schemas.Align) -> None:
    count = len(params.source_points)
    if count != len(params.target_points):
        flask.abort(400, "Source and target points must come in pairs")
    if mode == AFFINE and count != AFFINE_PAIRS:
        flask.abort(400, "Affine alignment needs 3 pairs of points")
    if mode == SIMILARITY and count not in SIMILARITY_PAIRS:
        flask.abort(400, "Alignment without distortion needs 1 or 2 pairs of points")


def _load_crs_object(data_id: str) -> tuple[Data, CrsGeodeObject]:
    data = geode_functions.get_data_info(data_id)
    geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
        geode_functions.data_file_path(data_id, data.native_file)
    )
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{data_id} does not support coordinate reference systems")
    return data, geode_object


def _coordinate_systems(
    mode: str, source_points: list[og.Point2D], target_points: list[og.Point2D]
) -> tuple[og.CoordinateSystem2D, og.CoordinateSystem2D, float | None, float | None]:
    """Frames moving source onto target, with the scale and rotation without distortion."""
    if mode == SIMILARITY:
        return _similarity_coordinate_systems(source_points, target_points)
    try:
        source = _coordinate_system(source_points)
        target = _coordinate_system(target_points)
    except RuntimeError:  # OpenGeode cannot build a coordinate system from colinear points
        flask.abort(400, "Points must not be colinear")
    return source, target, None, None


@dataclass(frozen=True)
class _Alignment:
    source: og.CoordinateSystem2D
    target: og.CoordinateSystem2D
    scale: float | None
    info: og_geosciences.GeographicCoordinateSystemInfo


def _apply_alignment(geode_object: CrsGeodeObject, alignment: _Alignment) -> None:
    from_active = _restart_alignment(geode_object)
    geode_object.create_crs("aligned", alignment.source, alignment.target)
    # The aligned CRS is active: scale its Z so the data keeps its proportions
    scale = alignment.scale
    if scale is not None and scale != 1 and isinstance(geode_object, CRS_GEODE_OBJECTS_3D):
        geode_object.scale_z(scale)
    if from_active:
        # The previous geographic CRS and its coordinates would clash with the new assignment
        _delete_other_crs(geode_object, "aligned", ORIGINAL_CRS)
    geode_object.assign_crs(alignment.info.authority_code(), alignment.info)


@typed_route(routes, schemas.align_route)
def align(params: schemas.Align) -> schemas.AlignResponse:
    data, geode_object = _load_crs_object(params.id)
    info = _known_info(geode_object, params.authority, params.code)
    mode = params.mode.value if params.mode is not None else SIMILARITY
    _check_pair_count(mode, params)
    # In degrees, a uniform scale would flatten Z and (lat, lon) axes would mirror the data
    if mode == SIMILARITY and not is_projected(params.authority, params.code):
        flask.abort(400, "Alignment without distortion needs a projected CRS: use the affine mode")
    # Linked data share the local frame of the aligned one
    linked = _linked_objects(params.id, params.linked_ids)
    source_points = _points(params.source_points)
    if geographic_info(geode_object.crs_manager()) is not None and _has_original_coordinates(
        geode_object
    ):
        source_points = _original_source_points(geode_object, params.source_points)
    source, target, scale, rotation = _coordinate_systems(
        mode, source_points, _points(params.target_points)
    )
    alignment = _Alignment(source, target, scale, info)
    _apply_alignment(geode_object, alignment)
    for _, _, linked_object in linked:
        _apply_alignment(linked_object, alignment)
    saved = utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    # The front rebuilds the local actors from the new light viewables
    response = _crs_response(saved)
    if scale is not None:
        response.update(scale=scale, rotation=rotation)
    if linked:
        response["linked"] = [
            {
                "id": data_id,
                **_crs_response(
                    utils_functions.save_all_viewables_and_return_info(
                        linked_object, linked_data, geode_functions.data_file_path(data_id)
                    )
                ),
            }
            for data_id, linked_data, linked_object in linked
        ]
    return schemas.AlignResponse.from_dict(response)

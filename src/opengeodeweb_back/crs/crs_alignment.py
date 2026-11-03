"""Georeferencing data from control points: similarity or affine alignment."""

from __future__ import annotations

# Standard library imports
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

# Third party imports
import opengeode as og

# Local application imports
from opengeodeweb_back.crs.crs_functions import (
    CRS_GEODE_OBJECTS_3D,
    ORIGINAL_CRS,
    CrsError,
    coordinate_system,
    geographic_info,
    original_coordinates,
)

if TYPE_CHECKING:
    from collections.abc import Sequence

    import opengeode_geosciences as og_geosciences

    from opengeodeweb_back.crs.crs_functions import CrsGeodeObject

SIMILARITY = "similarity"
AFFINE = "affine"
SIMILARITY_PAIRS = (1, 2)
AFFINE_PAIRS = 3


class ControlPoint(Protocol):
    x: float
    y: float


class SourcePoint(ControlPoint, Protocol):
    # Picked on the displayed data rather than typed
    picked: bool | None


@dataclass(frozen=True)
class Alignment:
    source: og.CoordinateSystem2D
    target: og.CoordinateSystem2D
    scale: float | None
    info: og_geosciences.GeographicCoordinateSystemInfo


def points(control_points: Sequence[ControlPoint]) -> list[og.Point2D]:
    return [og.Point2D([point.x, point.y]) for point in control_points]


def check_pair_count(mode: str, source_count: int, target_count: int) -> None:
    if source_count != target_count:
        msg = "Source and target points must come in pairs"
        raise CrsError(msg)
    if mode == AFFINE and source_count != AFFINE_PAIRS:
        msg = "Affine alignment needs 3 pairs of points"
        raise CrsError(msg)
    if mode == SIMILARITY and source_count not in SIMILARITY_PAIRS:
        msg = "Alignment without distortion needs 1 or 2 pairs of points"
        raise CrsError(msg)


def _crs_names(geode_object: CrsGeodeObject) -> set[str]:
    # Model components may hold different CRS: gather them all
    managers = [
        mesh.main_coordinate_reference_system_manager() for mesh in geode_object.crs_meshes()
    ]
    return {name for manager in managers for name in manager.coordinate_reference_system_names()}


def has_original_coordinates(geode_object: CrsGeodeObject) -> bool:
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


def source_points_in_original_coordinates(
    geode_object: CrsGeodeObject, source_points: Sequence[SourcePoint]
) -> list[og.Point2D]:
    """Source points in the loaded coordinates: alignments must not stack.

    Picked points lie on the displayed data: they are mapped back.
    Typed points are already original coordinates.
    """
    typed = points(source_points)
    if geographic_info(geode_object.crs_manager()) is None or not has_original_coordinates(
        geode_object
    ):
        return typed
    original_points = original_coordinates(geode_object, typed)
    if original_points is None:
        if any(point.picked for point in source_points):
            msg = "Data has no three non-colinear vertices to re-align"
            raise CrsError(msg)
        return typed
    return [
        original if source.picked else point
        for source, original, point in zip(source_points, original_points, typed, strict=True)
    ]


def _restart_alignment(geode_object: CrsGeodeObject) -> bool:
    """Go back to the loaded coordinates. True when only the active ones can be aligned."""
    if geographic_info(geode_object.crs_manager()) is None:
        return False
    if not has_original_coordinates(geode_object):
        return True
    geode_object.set_active_crs(ORIGINAL_CRS)
    _delete_other_crs(geode_object, ORIGINAL_CRS)
    return False


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
        msg = "The two points of the source or of the target must differ"
        raise CrsError(msg)
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


def colinear(frame_points: list[og.Point2D]) -> bool:
    origin, first, second = frame_points
    first_x = first.value(0) - origin.value(0)
    first_y = first.value(1) - origin.value(1)
    second_x = second.value(0) - origin.value(0)
    second_y = second.value(1) - origin.value(1)
    # Relative to the size of the triangle: coordinates may be in metres or millions of metres
    scale = max(math.hypot(first_x, first_y), math.hypot(second_x, second_y)) ** 2
    return scale == 0 or abs(first_x * second_y - first_y * second_x) <= 1e-12 * scale


def coordinate_systems(
    mode: str, source_points: list[og.Point2D], target_points: list[og.Point2D]
) -> tuple[og.CoordinateSystem2D, og.CoordinateSystem2D, float | None, float | None]:
    """Frames moving source onto target, with the scale and rotation without distortion."""
    if mode == SIMILARITY:
        return _similarity_coordinate_systems(source_points, target_points)
    # Checked here: any other error of OpenGeode is not the user's and is not hidden
    if colinear(source_points) or colinear(target_points):
        msg = "Points must not be colinear"
        raise CrsError(msg)
    return coordinate_system(source_points), coordinate_system(target_points), None, None


def apply_alignment(geode_object: CrsGeodeObject, alignment: Alignment) -> None:
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

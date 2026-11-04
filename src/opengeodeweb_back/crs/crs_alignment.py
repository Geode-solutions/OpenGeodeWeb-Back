"""Georeferencing data from control points: affine alignment."""

from __future__ import annotations

# Standard library imports
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

# Third party imports
import opengeode as og

# Local application imports
from opengeodeweb_back.crs.crs_functions import (
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
    info: og_geosciences.GeographicCoordinateSystemInfo


def points(control_points: Sequence[ControlPoint]) -> list[og.Point2D]:
    return [og.Point2D([point.x, point.y]) for point in control_points]


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
    source_points: list[og.Point2D], target_points: list[og.Point2D]
) -> tuple[og.CoordinateSystem2D, og.CoordinateSystem2D]:
    """Frames moving source onto target."""
    # Checked here: any other error of OpenGeode is not the user's and is not hidden
    if colinear(source_points) or colinear(target_points):
        msg = "Points must not be colinear"
        raise CrsError(msg)
    return coordinate_system(source_points), coordinate_system(target_points)


def apply_alignment(geode_object: CrsGeodeObject, alignment: Alignment) -> None:
    from_active = _restart_alignment(geode_object)
    geode_object.create_crs("aligned", alignment.source, alignment.target)
    if from_active:
        # The previous geographic CRS and its coordinates would clash with the new assignment
        _delete_other_crs(geode_object, "aligned", ORIGINAL_CRS)
    geode_object.assign_crs(alignment.info.authority_code(), alignment.info)

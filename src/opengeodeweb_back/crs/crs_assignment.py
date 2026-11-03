"""Assigning a geographic CRS to data, and converting data to another one."""

from __future__ import annotations

# Standard library imports
import logging
from typing import TYPE_CHECKING, Any

# Third party imports
import opengeode as og

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.crs.crs_functions import (
    ORIGINAL_CRS,
    CrsError,
    active_crs,
    coordinate_system,
    coordinates_implausible,
    geographic_info,
    known_info,
)

if TYPE_CHECKING:
    import opengeode_geosciences as og_geosciences
    from opengeodeweb_microservice.database.data import Data

    from opengeodeweb_back.crs.crs_functions import CrsGeodeObject

logger = logging.getLogger(__name__)


def prepare_crs_name(geode_object: CrsGeodeObject, crs_name: str) -> None:
    crs_manager = geode_object.crs_manager()
    info = geographic_info(crs_manager)
    if info is not None and info.authority_code() == crs_name:
        msg = f"{crs_name} is already the active CRS"
        raise CrsError(msg)
    # A registered inactive CRS may hold coordinates derived from an outdated label: recompute it
    if crs_manager.coordinate_reference_system_exists(crs_name):
        geode_object.delete_crs(crs_name)


def _keep_original_coordinates(geode_object: CrsGeodeObject) -> None:
    """Assigning renames the active CRS: assign a copy so "points" survives for re-align."""
    if not all(
        mesh.main_coordinate_reference_system_manager().active_coordinate_reference_system_name()
        == ORIGINAL_CRS
        for mesh in geode_object.crs_meshes()
    ):
        return
    identity = coordinate_system([og.Point2D([0, 0]), og.Point2D([1, 0]), og.Point2D([0, 1])])
    geode_object.create_crs("assigned", identity, identity)


def _assign(
    geode_object: CrsGeodeObject, authority: str, code: str
) -> og_geosciences.GeographicCoordinateSystemInfo:
    info = known_info(geode_object, authority, code)
    prepare_crs_name(geode_object, info.authority_code())
    _keep_original_coordinates(geode_object)
    geode_object.assign_crs(info.authority_code(), info)
    return info


def assign_all(
    targets: list[tuple[str, Data, CrsGeodeObject]],
    authority: str,
    code: str,
    *,
    only_plausible: bool,
) -> dict[str, dict[str, Any]]:
    """Assign the CRS to every target and save them. Per id: implausible, and crs if assigned.

    Without only_plausible, the plausibility is a warning only: the label is kept.
    """
    # Checked before any change: with only_plausible, an implausible data is left as it is
    implausible = {
        target_id: coordinates_implausible(
            target_object, known_info(target_object, authority, code)
        )
        for target_id, _, target_object in targets
    }
    assigned = {
        target_id for target_id, _, _ in targets if not (only_plausible and implausible[target_id])
    }
    # Every data is assigned in memory before any file is written
    for target_id, _, target_object in targets:
        if target_id in assigned:
            _assign(target_object, authority, code)
    # Assigning only relabels the coordinates: the viewables are unchanged
    for target_id, target_data, target_object in targets:
        if target_id in assigned:
            target_object.save(geode_functions.data_file_path(target_id, target_data.native_file))
    entries: dict[str, dict[str, Any]] = {}
    for target_id, _, target_object in targets:
        entry: dict[str, Any] = {"implausible": implausible[target_id]}
        if target_id in assigned:
            entry["crs"] = active_crs(target_object)
        entries[target_id] = entry
    return entries


def convert(geode_object: CrsGeodeObject, authority: str, code: str) -> None:
    if geographic_info(geode_object.crs_manager()) is None:
        msg = "Assign a geographic CRS before converting"
        raise CrsError(msg)
    info = known_info(geode_object, authority, code)
    prepare_crs_name(geode_object, info.authority_code())
    try:
        geode_object.convert_crs(info.authority_code(), info)
    except RuntimeError as error:
        # Usually PROJ rejecting coordinates outside the source or target CRS domain: the
        # Message tells, and the log keeps the trace for any other OpenGeode error
        logger.exception("Conversion to %s failed", info.authority_code())
        msg = f"Coordinates cannot be converted to {info.authority_code()}: {error}"
        raise CrsError(msg) from error

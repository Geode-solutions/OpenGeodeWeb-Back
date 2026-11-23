from __future__ import annotations

# Third party imports
import opengeode_geosciences as og_geosciences
import pytest

# Local application imports
from opengeodeweb_back.crs import crs_functions

LAMBERT = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "2154", "RGF93 v1 / Lambert-93")


def test_convert_xy_corners_to_wgs84_is_longitude_then_latitude() -> None:
    bounds = (651000.0, 6862000.0, 652000.0, 6863000.0)
    corners = crs_functions.convert_xy_corners(bounds, LAMBERT, crs_functions.WGS84)
    # Paris, around 2.3 E, 48.9 N
    assert corners[0] == pytest.approx((2.3321836844072203, 48.856172858823854))


def test_resolve_compound_crs_for_the_basemap() -> None:
    # The basemap is a 3D mesh: a compound CRS resolves like for any 3D data
    info = crs_functions.resolve_geographic_info(True, "EPSG", "2193+7839")  # noqa: FBT003
    assert info is not None
    assert info.authority_code() == "EPSG:2193+7839"
    assert crs_functions.resolve_geographic_info(False, "EPSG", "2193+7839").code == "2193"  # noqa: FBT003
    assert crs_functions.resolve_geographic_info(True, "EPSG", "2193+9999") is None  # noqa: FBT003

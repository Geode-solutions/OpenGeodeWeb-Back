from __future__ import annotations

# Standard library imports
import copy
from typing import TYPE_CHECKING

# Third party imports
import pytest

# Local application imports
from opengeodeweb_back import test_utils

if TYPE_CHECKING:
    from flask.testing import FlaskClient


@pytest.fixture
def point_data() -> test_utils.JsonData:
    return {"name": "test_point", "points": [{"x": 1.0, "y": 2.0, "z": 3.0}]}


@pytest.fixture
def curve_data() -> test_utils.JsonData:
    return {
        "name": "test_curve",
        "points": [{"x": 0.0, "y": 0.0, "z": 0.0}, {"x": 1.0, "y": 1.0, "z": 1.0}],
        "edges": [[0, 1]],
    }


@pytest.fixture
def surface_data() -> test_utils.JsonData:
    return {
        "name": "test_surface",
        "points": [
            {"x": 0.0, "y": 0.0, "z": 0.0},
            {"x": 1.0, "y": 0.0, "z": 0.0},
            {"x": 1.0, "y": 1.0, "z": 0.0},
            {"x": 0.0, "y": 1.0, "z": 0.0},
        ],
        "polygons": [[0, 1, 2, 3]],
    }


def test_create_point(client: FlaskClient, point_data: test_utils.JsonData) -> None:
    """Test the creation of a point with valid data."""
    route: str = "/opengeodeweb_back/create/point_set"

    # Test with all required data
    response = client.post(route, json=point_data)
    assert response.status_code == 200

    # Verify response data
    response_data = response.get_json()
    assert "viewable_file" in response_data
    assert "id" in response_data
    assert "name" in response_data
    assert "native_file" in response_data
    assert "viewer_type" in response_data
    assert "geode_object_type" in response_data

    assert response_data["name"] == point_data["name"]
    assert response_data["viewer_type"] == "mesh"
    assert response_data["geode_object_type"] == "PointSet3D"

    # Test with missing parameters
    test_utils.test_route_wrong_params(client, route, lambda: copy.deepcopy(point_data))


def test_create_point_set_multiple(client: FlaskClient) -> None:
    """Test the creation of a point set with multiple points."""
    route: str = "/opengeodeweb_back/create/point_set"
    data = {
        "name": "multiple_points",
        "points": [
            {"x": 1.0, "y": 2.0, "z": 3.0},
            {"x": 4.0, "y": 5.0, "z": 6.0},
            {"x": 7.0, "y": 8.0, "z": 9.0},
        ],
    }
    response = client.post(route, json=data)
    assert response.status_code == 200

    response_data = response.get_json()
    assert response_data["name"] == data["name"]
    assert response_data["geode_object_type"] == "PointSet3D"


def test_create_point_with_invalid_data(client: FlaskClient) -> None:
    """Test the point creation endpoint with invalid data."""
    route: str = "/opengeodeweb_back/create/point_set"

    # Test with non-numeric coordinates
    invalid_data: test_utils.JsonData = {
        "name": "invalid_point",
        "points": [{"x": "not_a_number", "y": 2.0, "z": 3.0}],
    }
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    # Test with missing coordinates
    invalid_data = {"name": "invalid_point", "points": [{"y": 2.0, "z": 3.0}]}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400


def test_create_curve(client: FlaskClient, curve_data: test_utils.JsonData) -> None:
    """Test the creation of a curve with valid data."""
    route: str = "/opengeodeweb_back/create/edged_curve"

    # Test with all required data
    response = client.post(route, json=curve_data)
    assert response.status_code == 200

    # Verify response data
    response_data = response.get_json()
    assert "viewable_file" in response_data
    assert "id" in response_data
    assert "name" in response_data
    assert "native_file" in response_data
    assert "viewer_type" in response_data
    assert "geode_object_type" in response_data

    assert response_data["name"] == curve_data["name"]
    assert response_data["viewer_type"] == "mesh"
    assert response_data["geode_object_type"] == "EdgedCurve3D"

    # Test with missing parameters
    test_utils.test_route_wrong_params(client, route, lambda: copy.deepcopy(curve_data))


def test_create_polygonal_surface(client: FlaskClient, surface_data: test_utils.JsonData) -> None:
    """Test the creation of a polygonal surface with valid data."""
    route: str = "/opengeodeweb_back/create/polygonal_surface"

    # Test with all required data
    response = client.post(route, json=surface_data)
    assert response.status_code == 200

    # Verify response data
    response_data = response.get_json()
    assert "viewable_file" in response_data
    assert "id" in response_data
    assert "name" in response_data
    assert "native_file" in response_data
    assert "viewer_type" in response_data
    assert "geode_object_type" in response_data

    assert response_data["name"] == surface_data["name"]
    assert response_data["viewer_type"] == "mesh"
    assert response_data["geode_object_type"] == "PolygonalSurface3D"

    # Test with missing parameters
    test_utils.test_route_wrong_params(client, route, lambda: copy.deepcopy(surface_data))


@pytest.fixture
def horizon_stack_data() -> test_utils.JsonData:
    return {
        "name": "test_horizon_stack",
        "horizons": ["Top", "Middle", "Bottom"],
        "unit_names": ["Above", "Upper", "Lower", "Below"],
    }


def test_create_horizon_stack(client: FlaskClient, horizon_stack_data: test_utils.JsonData) -> None:
    """Test the creation of a horizon stack from scratch, then read it back top to bottom."""
    route: str = "/opengeodeweb_back/create/horizon_stack"

    response = client.post(route, json=horizon_stack_data)
    assert response.status_code == 200

    response_data = response.get_json()
    assert response_data["name"] == horizon_stack_data["name"]
    assert response_data["geode_object_type"] == "HorizonStack3D"
    assert response_data["is_viewable"] is False

    info = client.post("/opengeodeweb_back/horizon_stack_info", json={"id": response_data["id"]})
    assert info.status_code == 200
    info_data = info.get_json()
    assert [horizon["name"] for horizon in info_data["horizons"]] == horizon_stack_data["horizons"]
    assert [unit["name"] for unit in info_data["units"]] == horizon_stack_data["unit_names"]

    test_utils.test_route_wrong_params(client, route, lambda: copy.deepcopy(horizon_stack_data))


def test_create_horizon_stack_without_unit_names(client: FlaskClient) -> None:
    """Unit names are optional: an empty list creates unnamed units."""
    route: str = "/opengeodeweb_back/create/horizon_stack"
    response = client.post(route, json={"name": "stack", "horizons": ["H1"], "unit_names": []})
    assert response.status_code == 200

    info = client.post(
        "/opengeodeweb_back/horizon_stack_info", json={"id": response.get_json()["id"]}
    )
    assert info.status_code == 200
    assert len(info.get_json()["units"]) == 2


def test_create_horizon_stack_wrong_unit_count(client: FlaskClient) -> None:
    """There must be one more unit than horizons."""
    route: str = "/opengeodeweb_back/create/horizon_stack"
    response = client.post(
        route, json={"name": "stack", "horizons": ["H1", "H2"], "unit_names": ["U1", "U2"]}
    )
    assert response.status_code == 400


def test_horizon_stack_info_wrong_type(
    client: FlaskClient, point_data: test_utils.JsonData
) -> None:
    """Reading the horizon stack of another object is a client error."""
    point_set = client.post("/opengeodeweb_back/create/point_set", json=point_data)
    info = client.post(
        "/opengeodeweb_back/horizon_stack_info", json={"id": point_set.get_json()["id"]}
    )
    assert info.status_code == 400

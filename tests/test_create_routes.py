# Standard library imports
import copy

# Third party imports
import pytest
from flask.testing import FlaskClient

# Local application imports
from opengeodeweb_back import test_utils


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


def test_create_polygonal_surface(
    client: FlaskClient, surface_data: test_utils.JsonData
) -> None:
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
    test_utils.test_route_wrong_params(
        client, route, lambda: copy.deepcopy(surface_data)
    )

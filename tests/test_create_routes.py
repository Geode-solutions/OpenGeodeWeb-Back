# Standard library imports
import os
import uuid
from typing import Any, Callable, Dict, List

# Third party imports
import pytest
from flask.testing import FlaskClient

# Local application imports
from opengeodeweb_back import test_utils


@pytest.fixture
def point_data() -> Dict[str, Any]:
    return {"name": "test_point", "x": 1.0, "y": 2.0, "z": 3.0}


@pytest.fixture
def aoi_data() -> Dict[str, Any]:
    return {
        "name": "test_aoi",
        "points": [
            {"x": 0.0, "y": 0.0},
            {"x": 1.0, "y": 0.0},
            {"x": 1.0, "y": 1.0},
            {"x": 0.0, "y": 1.0},
        ],
        "z": 0.0,
    }


@pytest.fixture
def voi_data() -> Dict[str, Any]:
    """Fixture for Volume of Interest (VOI) test data."""
    return {
        "name": "test_voi",
        "aoi_id": str(uuid.uuid4()),
        "z_min": -50.0,
        "z_max": 100.0,
        "id": str(uuid.uuid4()),
    }


def test_create_point(client: FlaskClient, point_data: Dict[str, Any]) -> None:
    """Test the creation of a point with valid data."""
    route: str = "/opengeodeweb_back/create/create_point"

    # Test with all required data
    response = client.post(route, json=point_data)
    assert response.status_code == 200

    # Verify response data
    response_data: Any = response.json
    assert "viewable_file_name" in response_data
    assert "id" in response_data
    assert "name" in response_data
    assert "native_file_name" in response_data
    assert "object_type" in response_data
    assert "geode_object" in response_data

    assert response_data["name"] == point_data["name"]
    assert response_data["object_type"] == "mesh"
    assert response_data["geode_object"] == "PointSet3D"

    # Test with missing parameters
    test_utils.test_route_wrong_params(client, route, lambda: point_data.copy())  # type: ignore


def test_create_aoi(client: FlaskClient, aoi_data: Dict[str, Any]) -> None:
    """Test the creation of an AOI with valid data."""
    route: str = "/opengeodeweb_back/create/create_aoi"

    # Test with all required data
    response = client.post(route, json=aoi_data)
    assert response.status_code == 200

    # Verify response data
    response_data: Any = response.json
    assert "viewable_file_name" in response_data
    assert "id" in response_data
    assert "name" in response_data
    assert "native_file_name" in response_data
    assert "object_type" in response_data
    assert "geode_object" in response_data

    assert response_data["name"] == aoi_data["name"]
    assert response_data["object_type"] == "mesh"
    assert response_data["geode_object"] == "EdgedCurve3D"

    # Test with missing parameters
    test_utils.test_route_wrong_params(client, route, lambda: aoi_data.copy())  # type: ignore


def test_create_voi(
    client: FlaskClient, aoi_data: Dict[str, Any], voi_data: Dict[str, Any]
) -> None:
    """Test the creation of a VOI with valid data (including optional id)."""
    aoi_route = "/opengeodeweb_back/create/create_aoi"
    aoi_response = client.post(aoi_route, json=aoi_data)
    assert aoi_response.status_code == 200
    aoi_id = aoi_response.json["id"]

    voi_data["aoi_id"] = aoi_id

    voi_route = "/opengeodeweb_back/create/create_voi"
    response = client.post(voi_route, json=voi_data)
    assert response.status_code == 200

    response_data = response.json
    assert "id" in response_data
    assert "name" in response_data
    assert response_data["name"] == voi_data["name"]
    assert response_data["object_type"] == "mesh"
    assert response_data["geode_object"] == "EdgedCurve3D"


def test_create_point_with_invalid_data(client: FlaskClient) -> None:
    """Test the point creation endpoint with invalid data."""
    route: str = "/opengeodeweb_back/create/create_point"

    # Test with non-numeric coordinates
    invalid_data: Dict[str, Any] = {
        "name": "invalid_point",
        "x": "not_a_number",
        "y": 2.0,
        "z": 3.0,
    }
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    # Test with missing coordinates
    invalid_data = {"name": "invalid_point", "y": 2.0, "z": 3.0}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400


def test_create_aoi_with_invalid_data(
    client: FlaskClient, aoi_data: Dict[str, Any]
) -> None:
    """Test the AOI creation endpoint with invalid data."""
    route: str = "/opengeodeweb_back/create/create_aoi"

    invalid_data: Dict[str, Any] = {
        **aoi_data,
        "points": [
            {"x": "not_a_number", "y": 0.0},
            {"x": 1.0, "y": 0.0},
            {"x": 1.0, "y": 1.0},
            {"x": 0.0, "y": 1.0},
        ],
    }
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    invalid_data = {**aoi_data, "points": [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}]}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    invalid_data = {**aoi_data, "z": "not_a_number"}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400


def test_create_voi_with_invalid_data(
    client: FlaskClient, aoi_data: Dict[str, Any], voi_data: Dict[str, Any]
) -> None:
    """Test the VOI creation endpoint with invalid data."""
    aoi_route = "/opengeodeweb_back/create/create_aoi"
    aoi_response = client.post(aoi_route, json=aoi_data)
    assert aoi_response.status_code == 200
    aoi_id = aoi_response.json["id"]

    route = "/opengeodeweb_back/create/create_aoi"

    invalid_data = {**voi_data, "aoi_id": aoi_id, "z_min": "not_a_number"}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    invalid_data = {**voi_data, "aoi_id": aoi_id, "z_max": "not_a_number"}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    invalid_data = {**voi_data, "aoi_id": 12345}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

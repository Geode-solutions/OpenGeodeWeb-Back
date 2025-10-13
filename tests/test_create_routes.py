# Standard library imports
import os
import uuid
from typing import Any, Callable, Dict, List

# Third party imports
import pytest
from flask.testing import FlaskClient

# Local application imports
from src.opengeodeweb_back import test_utils


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

    # Test with invalid points
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

    # Test with too few points
    invalid_data = {**aoi_data, "points": [{"x": 0.0, "y": 0.0}, {"x": 1.0, "y": 0.0}]}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400

    # Test with invalid z value
    invalid_data = {**aoi_data, "z": "not_a_number"}
    response = client.post(route, json=invalid_data)
    assert response.status_code == 400


def test_create_point_file_generation(
    client: FlaskClient, point_data: Dict[str, Any]
) -> None:
    """Test that the point creation generates the correct files."""
    route: str = "/opengeodeweb_back/create/create_point"

    # Make the request
    response = client.post(route, json=point_data)
    assert response.status_code == 200
    response_data: Any = response.json

    # Get the data folder path for this specific ID
    DATA_FOLDER_PATH: str = client.application.config["DATA_FOLDER_PATH"]
    data_id: str = response_data["id"]
    data_folder: str = os.path.join(DATA_FOLDER_PATH, data_id)

    # Check that the data folder exists
    assert os.path.exists(data_folder)
    assert os.path.isdir(data_folder)

    # Check native file exists
    native_file_path: str = os.path.join(data_folder, response_data["native_file_name"])
    assert os.path.exists(native_file_path)

    # Check viewable file exists
    viewable_file_path: str = os.path.join(
        data_folder, response_data["viewable_file_name"]
    )
    assert os.path.exists(viewable_file_path)

    # Check light viewable file exists if present
    if "binary_light_viewable" in response_data:
        light_viewable_file_path: str = os.path.join(data_folder, "light_viewable.vtp")
        assert os.path.exists(light_viewable_file_path)

    # Verify file extensions
    assert response_data["native_file_name"].endswith(".og_pts3d")
    assert response_data["viewable_file_name"].endswith(".vtp")


def test_create_aoi_file_generation(
    client: FlaskClient, aoi_data: Dict[str, Any]
) -> None:
    """Test that the AOI creation generates the correct files."""
    route: str = "/opengeodeweb_back/create/create_aoi"

    # Make the request
    response = client.post(route, json=aoi_data)
    assert response.status_code == 200
    response_data: Any = response.json

    # Get the data folder path for this specific ID
    DATA_FOLDER_PATH: str = client.application.config["DATA_FOLDER_PATH"]
    data_id: str = response_data["id"]
    data_folder: str = os.path.join(DATA_FOLDER_PATH, data_id)

    # Check that the data folder exists
    assert os.path.exists(data_folder)
    assert os.path.isdir(data_folder)

    # Check native file exists
    native_file_path: str = os.path.join(data_folder, response_data["native_file_name"])
    assert os.path.exists(native_file_path)

    # Check viewable file exists
    viewable_file_path: str = os.path.join(
        data_folder, response_data["viewable_file_name"]
    )
    assert os.path.exists(viewable_file_path)

    # Check light viewable file exists if present
    if "binary_light_viewable" in response_data:
        light_viewable_file_path: str = os.path.join(data_folder, "light_viewable.vtp")
        assert os.path.exists(light_viewable_file_path)

    # Verify file extensions
    assert response_data["native_file_name"].endswith(".og_edc3d")
    assert response_data["viewable_file_name"].endswith(".vtp")

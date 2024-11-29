# Standard library imports
import base64
import os

# Third party imports
from werkzeug.datastructures import FileStorage

# Local application imports
from src.opengeodeweb_back import test_utils


def test_allowed_files(client):
    route = f"/allowed_files"
    get_full_data = lambda: {"supported_feature": "None"}
    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200
    extensions = response.json["extensions"]
    assert type(extensions) is list
    for extension in extensions:
        assert type(extension) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_allowed_objects(client):
    route = f"/allowed_objects"

    def get_full_data():
        return {
            "filename": "corbi.og_brep",
            "supported_feature": None,
        }

    # Normal test with filename 'corbi.og_brep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    allowed_objects = response.json["allowed_objects"]
    assert type(allowed_objects) is dict
    for allowed_object in allowed_objects:
        assert type(allowed_object) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_upload_file(client):
    response = client.put(
        f"/upload_file",
        data={"file": FileStorage(open("./tests/corbi.og_brep", "rb"))},
    )

    assert response.status_code == 201


def test_missing_files(client):
    route = f"/missing_files"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "corbi.og_brep",
        }

    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200
    has_missing_files = response.json["has_missing_files"]
    mandatory_files = response.json["mandatory_files"]
    additional_files = response.json["additional_files"]
    assert type(has_missing_files) is bool
    assert type(mandatory_files) is list
    assert type(additional_files) is list

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_geographic_coordinate_systems(client):
    route = f"/geographic_coordinate_systems"
    get_full_data = lambda: {"input_geode_object": "BRep"}
    # Normal test with geode_object 'BRep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    crs_list = response.json["crs_list"]
    assert type(crs_list) is list
    for crs in crs_list:
        assert type(crs) is dict

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_inspect_file(client):
    route = f"/inspect_file"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "corbi.og_brep",
        }

    json = get_full_data()

    # Normal test with geode_object 'BRep'
    response = client.post(route, json=json)
    assert response.status_code == 200
    inspection_result = response.json["inspection_result"]
    assert type(inspection_result) is dict

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_geode_objects_and_output_extensions(client):
    route = "/geode_objects_and_output_extensions"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "corbi.og_brep",
        }

    response = client.post(route, json=get_full_data())

    assert response.status_code == 200
    geode_objects_and_output_extensions = response.json[
        "geode_objects_and_output_extensions"
    ]
    assert type(geode_objects_and_output_extensions) is dict
    for geode_object, values in geode_objects_and_output_extensions.items():
        assert type(values) is dict
        for output_extension, value in values.items():
            assert type(value) is dict
            assert type(value["is_saveable"]) is bool

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_save_viewable_file(client):
    route = f"/save_viewable_file"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "corbi.og_brep",
        }

    # Normal test with filename 'corbi.og_brep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    name = response.json["name"]
    assert type(name) is str
    native_file_name = response.json["native_file_name"]
    assert type(native_file_name) is str
    viewable_file_name = response.json["viewable_file_name"]
    assert type(viewable_file_name) is str
    id = response.json["id"]
    assert type(id) is str
    object_type = response.json["object_type"]
    assert type(object_type) is str
    assert object_type in ["model", "mesh"]

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_vertex_attribute_names(client):
    response = client.put(
        f"/upload_file",
        data={"file": FileStorage(open("./tests/vertex_attribute.vtp", "rb"))},
    )
    assert response.status_code == 201

    route = f"/vertex_attribute_names"

    def get_full_data():
        return {
            "input_geode_object": "PolygonalSurface3D",
            "filename": "vertex_attribute.vtp",
        }

    # Normal test with filename 'vertex_attribute.vtp'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    vertex_attribute_names = response.json["vertex_attribute_names"]
    assert type(vertex_attribute_names) is list
    for vertex_attribute_name in vertex_attribute_names:
        assert type(vertex_attribute_name) is str

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_polygon_attribute_names(client):
    response = client.put(
        f"/upload_file",
        data={"file": FileStorage(open("./tests/polygon_attribute.vtp", "rb"))},
    )
    assert response.status_code == 201

    route = f"/polygon_attribute_names"

    def get_full_data():
        return {
            "input_geode_object": "PolygonalSurface3D",
            "filename": "polygon_attribute.vtp",
        }

    # Normal test with filename 'vertex_attribute.vtp'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    polygon_attribute_names = response.json["polygon_attribute_names"]
    assert type(polygon_attribute_names) is list
    for polygon_attribute_name in polygon_attribute_names:
        assert type(polygon_attribute_name) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_create_point(client):
    route = f"/create_point"
    get_full_data = lambda: {"x": 1, "y": 2, "z": 3}

    # Normal test with all keys
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    viewable_file_name = response.json["viewable_file_name"]
    assert type(viewable_file_name) is str
    id = response.json["id"]
    assert type(id) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)

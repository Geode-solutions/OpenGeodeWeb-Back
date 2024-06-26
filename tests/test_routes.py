import os
import base64
from werkzeug.datastructures import FileStorage


def test_allowed_files(client):
    route = f"/allowed_files"
    response = client.post(route, json={"supported_feature": None})
    assert response.status_code == 200
    extensions = response.json["extensions"]
    assert type(extensions) is list
    for extension in extensions:
        assert type(extension) is str


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

    for key, value in get_full_data().items():
        json = get_full_data()
        json.pop(key)
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.json["description"]
        assert error_description == f"Validation error: '{key}' is a required property"


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
    response = client.post(
        route,
        json=json,
    )

    assert response.status_code == 200
    has_missing_files = response.json["has_missing_files"]
    mandatory_files = response.json["mandatory_files"]
    additional_files = response.json["additional_files"]
    assert type(has_missing_files) is bool
    assert type(mandatory_files) is list
    assert type(additional_files) is list

    for key, value in get_full_data().items():
        json = get_full_data()
        json.pop(key)
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.json["description"]
        assert error_description == f"Validation error: '{key}' is a required property"


def test_geographic_coordinate_systems(client):
    route = f"/geographic_coordinate_systems"

    # Normal test with geode_object 'BRep'
    response = client.post(route, json={"input_geode_object": "BRep"})
    assert response.status_code == 200
    crs_list = response.json["crs_list"]
    assert type(crs_list) is list
    for crs in crs_list:
        assert type(crs) is dict

    # Test without geode_object
    response = client.post(route, json={})
    assert response.status_code == 400
    error_message = response.json["description"]
    assert (
        error_message == "Validation error: 'input_geode_object' is a required property"
    )


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

    for key, value in get_full_data().items():
        json = get_full_data()
        json.pop(key)
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.json["description"]
        assert error_description == f"Validation error: '{key}' is a required property"


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

    # Test without input_geode_object
    response = client.post(route, json={})
    assert response.status_code == 400
    error_message = response.json["description"]
    assert (
        error_message == "Validation error: 'input_geode_object' is a required property"
    )


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

    for key, value in get_full_data().items():
        json = get_full_data()
        json.pop(key)
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.json["description"]
        assert error_description == f"Validation error: '{key}' is a required property"

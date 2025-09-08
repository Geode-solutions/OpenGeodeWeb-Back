# Standard library imports
import os
import shutil

# Third party imports
from werkzeug.datastructures import FileStorage

# Local application imports
from src.opengeodeweb_back import geode_functions, test_utils
from src.opengeodeweb_back.data import Data
from src.opengeodeweb_back.database import database


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


def test_upload_file(client, filename="test.og_brep"):
    response = client.put(
        f"/upload_file",
        data={"file": FileStorage(open(f"./tests/data/{filename}", "rb"))},
    )
    assert response.status_code == 201


def test_missing_files(client):
    route = f"/missing_files"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "test.og_brep",
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
    test_upload_file(client, filename="corbi.og_brep")
    route = f"/save_viewable_file"

    def get_full_data():
        return {
            "input_geode_object": "BRep",
            "filename": "corbi.og_brep",
        }

    # Normal test with filename 'corbi.og_brep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    native_file_name = response.json["native_file_name"]
    assert type(native_file_name) is str
    viewable_file_name = response.json["viewable_file_name"]
    assert type(viewable_file_name) is str
    id = response.json.get("id")
    assert type(id) is str
    object_type = response.json["object_type"]
    assert type(object_type) is str
    assert object_type in ["model", "mesh"]
    binary_light_viewable = response.json["binary_light_viewable"]
    assert type(binary_light_viewable) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_texture_coordinates(client, test_id):
    with client.application.app_context():
        data = Data.create(geode_object="PolygonalSurface3D", input_file="hat.vtp")
        data.native_file_name = "hat.vtp"
        database.session.commit()

        data_path = geode_functions.data_file_path(data.id, "hat.vtp")
        print(data_path)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy("./tests/data/hat.vtp", data_path)

    response = client.post(
        "/texture_coordinates",
        json={"id": data.id},
    )
    assert response.status_code == 200
    texture_coordinates = response.json["texture_coordinates"]
    assert type(texture_coordinates) is list
    for texture_coordinate in texture_coordinates:
        assert type(texture_coordinate) is str


def test_vertex_attribute_names(client, test_id):
    route = f"/vertex_attribute_names"

    with client.application.app_context():
        data = Data.create(geode_object="PolygonalSurface3D", input_file="test.vtp")
        data.native_file_name = "test.vtp"
        database.session.commit()

        data_path = geode_functions.data_file_path(data.id, "test.vtp")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        if os.path.exists("./tests/data/hat.vtp"):
            shutil.copy("./tests/data/hat.vtp", data_path)

    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    vertex_attribute_names = response.json["vertex_attribute_names"]
    assert type(vertex_attribute_names) is list
    for vertex_attribute_name in vertex_attribute_names:
        assert type(vertex_attribute_name) is str


def test_polygon_attribute_names(client, test_id):
    route = f"/polygon_attribute_names"

    with client.application.app_context():
        data = Data.create(geode_object="PolygonalSurface3D", input_file="test.vtp")
        data.native_file_name = "test.vtp"
        database.session.commit()

        data_path = geode_functions.data_file_path(data.id, "test.vtp")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
    shutil.copy("./tests/data/test.vtp", data_path)

    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    polygon_attribute_names = response.json["polygon_attribute_names"]
    assert type(polygon_attribute_names) is list
    for polygon_attribute_name in polygon_attribute_names:
        assert type(polygon_attribute_name) is str


def test_polyhedron_attribute_names(client, test_id):
    route = f"/polyhedron_attribute_names"

    with client.application.app_context():
        data = Data.create(geode_object="PolyhedralSolid3D", input_file="test.vtu")
        data.native_file_name = "test.vtu"
        database.session.commit()

        data_path = geode_functions.data_file_path(data.id, "test.vtu")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy("./tests/data/test.vtu", data_path)

    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    polyhedron_attribute_names = response.json["polyhedron_attribute_names"]
    assert type(polyhedron_attribute_names) is list
    for polyhedron_attribute_name in polyhedron_attribute_names:
        assert type(polyhedron_attribute_name) is str


def test_create_point(client):
    route = f"/create_point"
    get_full_data = lambda: {"title": "test_point", "x": 1, "y": 2, "z": 3}

    # Normal test with all keys
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    viewable_file_name = response.json["viewable_file_name"]
    assert type(viewable_file_name) is str
    id = response.json.get("id")
    assert type(id) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_database_uri_path(client):
    app = client.application
    with app.app_context():
        base_dir = os.path.abspath(os.path.dirname(__file__))
        expected_db_path = os.path.join(base_dir, "data", "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

        assert os.path.exists(expected_db_path)

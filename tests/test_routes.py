# Standard library imports
import os

# Third party imports
from werkzeug.datastructures import FileStorage

# Local application imports
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_back import geode_functions, test_utils

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_allowed_files(client):
    route = f"/opengeodeweb_back/allowed_files"
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
    route = f"/opengeodeweb_back/allowed_objects"

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
    file = os.path.join(data_dir, filename)
    print(f"{file=}", flush=True)
    response = client.put(
        f"/opengeodeweb_back/upload_file",
        data={"file": FileStorage(open(file, "rb"))},
    )
    assert response.status_code == 201


def test_missing_files(client):
    route = f"/opengeodeweb_back/missing_files"

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
    route = f"/opengeodeweb_back/geographic_coordinate_systems"
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
    route = f"/opengeodeweb_back/inspect_file"

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
    route = "/opengeodeweb_back/geode_objects_and_output_extensions"

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
    route = f"/opengeodeweb_back/save_viewable_file"

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
        file = os.path.join(data_dir, "hat.vtp")
        data = Data.create(
            geode_object="PolygonalSurface3D",
            viewer_object=geode_functions.get_object_type("PolygonalSurface3D"),
            input_file=file,
        )
        data.native_file_name = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file_name)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(
        "/opengeodeweb_back/texture_coordinates", json={"id": data.id}
    )
    assert response.status_code == 200
    texture_coordinates = response.json["texture_coordinates"]
    assert type(texture_coordinates) is list
    for texture_coordinate in texture_coordinates:
        assert type(texture_coordinate) is str


def test_vertex_attribute_names(client, test_id):
    route = f"/opengeodeweb_back/vertex_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtp")
        data = Data.create(
            geode_object="PolygonalSurface3D",
            viewer_object=geode_functions.get_object_type("PolygonalSurface3D"),
            input_file=file,
        )
        data.native_file_name = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file_name)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    vertex_attribute_names = response.json["vertex_attribute_names"]
    assert type(vertex_attribute_names) is list
    for vertex_attribute_name in vertex_attribute_names:
        assert type(vertex_attribute_name) is str


def test_polygon_attribute_names(client, test_id):
    route = f"/opengeodeweb_back/polygon_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtp")
        data = Data.create(
            geode_object="PolygonalSurface3D",
            viewer_object=geode_functions.get_object_type("PolygonalSurface3D"),
            input_file=file,
        )
        data.native_file_name = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file_name)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    polygon_attribute_names = response.json["polygon_attribute_names"]
    assert type(polygon_attribute_names) is list
    for polygon_attribute_name in polygon_attribute_names:
        assert type(polygon_attribute_name) is str


def test_polyhedron_attribute_names(client, test_id):
    route = f"/opengeodeweb_back/polyhedron_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtu")
        data = Data.create(
            geode_object="PolyhedralSolid3D",
            viewer_object=geode_functions.get_object_type("PolyhedralSolid3D"),
            input_file=file,
        )
        data.native_file_name = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file_name)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    print(response.json)
    assert response.status_code == 200
    polyhedron_attribute_names = response.json["polyhedron_attribute_names"]
    assert type(polyhedron_attribute_names) is list
    for polyhedron_attribute_name in polyhedron_attribute_names:
        assert type(polyhedron_attribute_name) is str


def test_database_uri_path(client):
    app = client.application
    with app.app_context():
        base_dir = os.path.abspath(os.path.dirname(__file__))
        expected_db_path = os.path.join(base_dir, "data", "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

        assert os.path.exists(expected_db_path)

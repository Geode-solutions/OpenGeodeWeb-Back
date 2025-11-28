# Standard library imports
import os

# Third party imports
from werkzeug.datastructures import FileStorage
from flask.testing import FlaskClient

# Local application imports
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_back import geode_functions, test_utils
from opengeodeweb_back.geode_objects.geode_polygonal_surface3d import (
    GeodePolygonalSurface3D,
)
from opengeodeweb_back.geode_objects.geode_polyhedral_solid3d import (
    GeodePolyhedralSolid3D,
)

from opengeodeweb_back.geode_objects.geode_regular_grid2d import (
    GeodeRegularGrid2D,
)

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_allowed_files(client: FlaskClient) -> None:
    route = f"/opengeodeweb_back/allowed_files"

    def get_full_data() -> test_utils.JsonData:
        return {}

    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200
    extensions = response.get_json()["extensions"]
    assert type(extensions) is list
    for extension in extensions:
        assert type(extension) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_allowed_objects(client: FlaskClient) -> None:
    route = f"/opengeodeweb_back/allowed_objects"

    def get_full_data() -> test_utils.JsonData:
        return {
            "filename": "corbi.og_brep",
        }

    # Normal test with filename 'corbi.og_brep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    allowed_objects = response.get_json()["allowed_objects"]
    assert type(allowed_objects) is dict
    for allowed_object in allowed_objects:
        assert type(allowed_object) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_upload_file(client: FlaskClient, filename: str = "test.og_brep") -> None:
    file = os.path.join(data_dir, filename)
    print(f"{file=}", flush=True)
    response = client.put(
        f"/opengeodeweb_back/upload_file",
        data={"file": FileStorage(open(file, "rb"))},
    )
    assert response.status_code == 201


def test_missing_files(client: FlaskClient) -> None:
    route = f"/opengeodeweb_back/missing_files"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
            "filename": "test.og_brep",
        }

    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200
    has_missing_files = response.get_json()["has_missing_files"]
    mandatory_files = response.get_json()["mandatory_files"]
    additional_files = response.get_json()["additional_files"]
    assert type(has_missing_files) is bool
    assert type(mandatory_files) is list
    assert type(additional_files) is list

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_geographic_coordinate_systems(client: FlaskClient) -> None:
    route = f"/opengeodeweb_back/geographic_coordinate_systems"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
        }

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    crs_list = response.get_json()["crs_list"]
    assert type(crs_list) is list
    for crs in crs_list:
        assert type(crs) is dict

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_inspect_file(client: FlaskClient) -> None:
    route = f"/opengeodeweb_back/inspect_file"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
            "filename": "corbi.og_brep",
        }

    json = get_full_data()

    # Normal test with geode_object 'BRep'
    response = client.post(route, json=json)
    assert response.status_code == 200
    inspection_result = response.get_json()["inspection_result"]
    assert type(inspection_result) is dict

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_geode_objects_and_output_extensions(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/geode_objects_and_output_extensions"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
            "filename": "corbi.og_brep",
        }

    response = client.post(route, json=get_full_data())

    assert response.status_code == 200
    geode_objects_and_output_extensions = response.get_json()[
        "geode_objects_and_output_extensions"
    ]
    assert type(geode_objects_and_output_extensions) is dict
    for geode_object, values in geode_objects_and_output_extensions.items():
        assert type(values) is dict
        for output_extension, value in values.items():
            assert type(value) is bool

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_save_viewable_file(client: FlaskClient) -> None:
    test_upload_file(client, filename="corbi.og_brep")
    route = f"/opengeodeweb_back/save_viewable_file"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
            "filename": "corbi.og_brep",
        }

    # Normal test with filename 'corbi.og_brep'
    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    native_file = response.get_json()["native_file"]
    assert type(native_file) is str
    viewable_file = response.get_json()["viewable_file"]
    assert type(viewable_file) is str
    id = response.get_json().get("id")
    assert type(id) is str
    object_type = response.get_json()["viewer_type"]
    assert type(object_type) is str
    assert object_type in ["model", "mesh"]
    binary_light_viewable = response.get_json()["binary_light_viewable"]
    assert type(binary_light_viewable) is str

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_texture_coordinates(client: FlaskClient, test_id: str) -> None:
    with client.application.app_context():
        file = os.path.join(data_dir, "hat.vtp")
        data = Data.create(
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            input_file=file,
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(
        "/opengeodeweb_back/texture_coordinates", json={"id": data.id}
    )
    assert response.status_code == 200
    texture_coordinates = response.get_json()["texture_coordinates"]
    assert type(texture_coordinates) is list
    for texture_coordinate in texture_coordinates:
        assert type(texture_coordinate) is str


def test_vertex_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/vertex_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtp")
        data = Data.create(
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            input_file=file,
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    vertex_attribute_names = response.get_json()["vertex_attribute_names"]
    assert type(vertex_attribute_names) is list
    for vertex_attribute_name in vertex_attribute_names:
        assert type(vertex_attribute_name) is str


def test_cell_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/cell_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.og_rgd2d")
        data = Data.create(
            geode_object=GeodeRegularGrid2D.geode_object_type(),
            viewer_object=GeodeRegularGrid2D.viewer_type(),
            input_file=file,
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    cell_attribute_names = response.get_json()["cell_attribute_names"]
    assert type(cell_attribute_names) is list
    for cell_attribute_name in cell_attribute_names:
        assert type(cell_attribute_name) is str


def test_polygon_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polygon_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtp")
        data = Data.create(
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            input_file=file,
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    polygon_attribute_names = response.get_json()["polygon_attribute_names"]
    assert type(polygon_attribute_names) is list
    for polygon_attribute_name in polygon_attribute_names:
        assert type(polygon_attribute_name) is str


def test_polyhedron_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polyhedron_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtu")
        data = Data.create(
            geode_object=GeodePolyhedralSolid3D.geode_object_type(),
            viewer_object=GeodePolyhedralSolid3D.viewer_type(),
            input_file=file,
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = geode_functions.data_file_path(data.id, data.native_file)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        assert os.path.exists(data_path), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    print(response.get_json())
    assert response.status_code == 200
    polyhedron_attribute_names = response.get_json()["polyhedron_attribute_names"]
    assert type(polyhedron_attribute_names) is list
    for polyhedron_attribute_name in polyhedron_attribute_names:
        assert type(polyhedron_attribute_name) is str


def test_database_uri_path(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        base_dir = os.path.abspath(os.path.dirname(__file__))
        expected_db_path = os.path.join(base_dir, "data", "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

        assert os.path.exists(expected_db_path)

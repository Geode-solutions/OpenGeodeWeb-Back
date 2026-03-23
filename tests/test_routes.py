# Standard library imports
import os

# Third party imports
from werkzeug.datastructures import FileStorage
from flask.testing import FlaskClient
from werkzeug.test import TestResponse
from pathlib import Path
import json
import zipfile

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
from opengeodeweb_back.geode_objects.geode_edged_curve3d import (
    GeodeEdgedCurve3D,
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


def test_save_viewable_file(
    client: FlaskClient,
    geode_object_type: str = "BRep",
    filename: str = "corbi.og_brep",
) -> TestResponse:
    test_upload_file(client, filename)
    route = f"/opengeodeweb_back/save_viewable_file"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": geode_object_type,
            "filename": filename,
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
    return response


def test_texture_coordinates(client: FlaskClient, test_id: str) -> None:
    with client.application.app_context():
        file = os.path.join(data_dir, "hat.vtp")
        data = Data.create(
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
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
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
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
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute


def test_cell_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/cell_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.og_rgd2d")
        data = Data.create(
            geode_object=GeodeRegularGrid2D.geode_object_type(),
            viewer_object=GeodeRegularGrid2D.viewer_type(),
            viewer_elements_type=GeodeRegularGrid2D.viewer_elements_type(),
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
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute


def test_polygon_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polygon_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtp")
        data = Data.create(
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
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
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute


def test_polyhedron_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polyhedron_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.vtu")
        data = Data.create(
            geode_object=GeodePolyhedralSolid3D.geode_object_type(),
            viewer_object=GeodePolyhedralSolid3D.viewer_type(),
            viewer_elements_type=GeodePolyhedralSolid3D.viewer_elements_type(),
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
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        if attribute["attribute_name"] == "Range":
            assert attribute["min_value"] == 0.0
            assert attribute["max_value"] == 579.0


def test_edge_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/edge_attribute_names"

    with client.application.app_context():
        file = os.path.join(data_dir, "test.og_edc3d")
        data = Data.create(
            geode_object=GeodeEdgedCurve3D.geode_object_type(),
            viewer_object=GeodeEdgedCurve3D.viewer_type(),
            viewer_elements_type=GeodeEdgedCurve3D.viewer_elements_type(),
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
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute


def test_database_uri_path(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        base_dir = os.path.abspath(os.path.dirname(__file__))
        expected_db_path = os.path.join(base_dir, "data", "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

        assert os.path.exists(expected_db_path)


def test_geode_object_inheritance(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/geode_object_inheritance"
    # Test BRep
    response = client.post(route, json={"geode_object_type": "BRep"})
    assert response.status_code == 200
    json_data = response.get_json()
    parents = json_data["parents"]
    children = json_data["children"]
    assert "BRep" not in parents
    assert "BRep" not in children
    # Descendants
    assert "StructuralModel" in children
    assert "ImplicitStructuralModel" in children

    # Test CrossSection
    response = client.post(route, json={"geode_object_type": "CrossSection"})
    assert response.status_code == 200
    json_data = response.get_json()
    parents = json_data["parents"]
    children = json_data["children"]
    assert "CrossSection" not in parents
    assert "CrossSection" not in children
    # Parent
    assert "Section" in parents
    # Descendant
    assert "ImplicitCrossSection" in children

    # Test PolyhedralSolid3D
    response = client.post(route, json={"geode_object_type": "PolyhedralSolid3D"})
    assert response.status_code == 200
    json_data = response.get_json()
    parents = json_data["parents"]
    children = json_data["children"]
    assert "PolyhedralSolid3D" not in parents
    assert "PolyhedralSolid3D" not in children
    # Parent
    assert "VertexSet" in parents

    # Test all params
    def get_full_data() -> test_utils.JsonData:
        return {"geode_object_type": "BRep"}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_model_components(client: FlaskClient) -> None:
    geode_object_type = "BRep"
    filename = "LS2.og_brep"
    response = test_save_viewable_file(client, geode_object_type, filename)
    assert response.status_code == 200
    assert "mesh_components" in response.get_json()
    mesh_components = response.get_json()["mesh_components"]
    assert isinstance(mesh_components, list)
    assert len(mesh_components) > 0
    name_is_uuid = False
    name_is_not_uuid = False
    for mesh_component in mesh_components:
        assert isinstance(mesh_component, object)
        assert isinstance(mesh_component["geode_id"], str)
        assert isinstance(mesh_component["viewer_id"], int)
        assert isinstance(mesh_component["name"], str)
        assert isinstance(mesh_component["type"], str)
        if mesh_component["name"] == mesh_component["geode_id"]:
            name_is_uuid = True
        else:
            name_is_not_uuid = True
        assert isinstance(mesh_component["boundaries"], list)
        for boundary_uuid in mesh_component["boundaries"]:
            assert isinstance(boundary_uuid, str)
        assert isinstance(mesh_component["internals"], list)
        for internal_uuid in mesh_component["internals"]:
            assert isinstance(internal_uuid, str)
    assert name_is_uuid is True
    assert name_is_not_uuid is True
    assert "collection_components" in response.get_json()
    collection_components = response.get_json()["collection_components"]
    assert isinstance(collection_components, list)
    for collection_component in collection_components:
        assert isinstance(collection_component, object)
        assert isinstance(collection_component["geode_id"], str)
        assert isinstance(collection_component["name"], str)
        assert isinstance(collection_component["items"], list)
        for item_uuid in collection_component["items"]:
            assert isinstance(item_uuid, str)


def test_export_project_route(client: FlaskClient, tmp_path: Path) -> None:
    route = "/opengeodeweb_back/export_project"
    snapshot = {
        "styles": {"1": {"visibility": True, "opacity": 1.0, "color": [0.2, 0.6, 0.9]}}
    }
    filename = "export_project_test.vease"
    project_folder = client.application.config["DATA_FOLDER_PATH"]
    os.makedirs(project_folder, exist_ok=True)
    database_root_path = os.path.join(project_folder, "project.db")
    with open(database_root_path, "wb") as f:
        f.write(b"test_project_db")

    with get_session() as session:
        session.query(Data).delete()
        session.commit()

        data1 = Data(
            id="test_data_1",
            geode_object="BRep",
            viewer_object="BRep",
            viewer_elements_type="default",
            native_file="native.txt",
        )
        data2 = Data(
            id="test_data_2",
            geode_object="Section",
            viewer_object="Section",
            viewer_elements_type="default",
            native_file="native.txt",
        )
        session.add(data1)
        session.add(data2)
        session.commit()

        data1_dir = os.path.join(project_folder, "test_data_1")
        os.makedirs(data1_dir, exist_ok=True)
        with open(os.path.join(data1_dir, "native.txt"), "w") as f:
            f.write("native file content")

        data2_dir = os.path.join(project_folder, "test_data_2")
        os.makedirs(data2_dir, exist_ok=True)
        with open(os.path.join(data2_dir, "native.txt"), "w") as f:
            f.write("native file content")

    response = client.post(route, json={"snapshot": snapshot, "filename": filename})
    assert response.status_code == 200
    assert response.headers.get("new-file-name") == filename
    assert response.mimetype == "application/octet-binary"
    response.direct_passthrough = False
    zip_bytes = response.get_data()
    tmp_zip_path = tmp_path / filename
    tmp_zip_path.write_bytes(zip_bytes)

    with zipfile.ZipFile(tmp_zip_path, "r") as zip_file:
        names = zip_file.namelist()
        assert "snapshot.json" in names
        parsed = json.loads(zip_file.read("snapshot.json").decode("utf-8"))
        assert parsed == snapshot
        assert "project.db" in names
        assert "test_data_1/native.txt" in names
        assert "test_data_2/native.txt" in names

    response.close()

    export_path = os.path.join(project_folder, filename)
    if os.path.exists(export_path):
        os.remove(export_path)


def test_import_project_route(client: FlaskClient, tmp_path: Path) -> None:
    route = "/opengeodeweb_back/import_project"
    snapshot = {
        "styles": {"1": {"visibility": True, "opacity": 1.0, "color": [0.2, 0.6, 0.9]}}
    }

    original_data_folder = client.application.config["DATA_FOLDER_PATH"]
    client.application.config["DATA_FOLDER_PATH"] = os.path.join(
        str(tmp_path), "project_data"
    )
    db_path = os.path.join(client.application.config["DATA_FOLDER_PATH"], "project.db")

    import sqlite3, zipfile, json

    temp_db = tmp_path / "temp_project.db"
    conn = sqlite3.connect(str(temp_db))
    conn.execute(
        "CREATE TABLE datas (id TEXT PRIMARY KEY, geode_object TEXT, viewer_object TEXT, viewer_elements_type TEXT, native_file TEXT, "
        "viewable_file TEXT, light_viewable_file TEXT)"
    )
    conn.commit()
    conn.close()

    z = tmp_path / "import_project_test.vease"
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("snapshot.json", json.dumps(snapshot))
        zipf.write(str(temp_db), "project.db")

    with open(z, "rb") as f:
        resp = client.post(
            route,
            data={"file": (f, "import_project_test.vease")},
            content_type="multipart/form-data",
        )

    assert resp.status_code == 200
    assert resp.get_json().get("snapshot") == snapshot
    assert os.path.exists(db_path)

    from opengeodeweb_microservice.database import connection

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder
    test_db_path = os.environ.get("TEST_DB_PATH")
    if test_db_path:
        connection.init_database(test_db_path, create_tables=True)

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder


def test_save_viewable_workflow_from_object(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/create/point"
    point_data = {
        "name": "workflow_point_3d",
        "x": 0.0,
        "y": 0.0,
        "z": 0.0,
    }

    response = client.post(route, json=point_data)
    assert response.status_code == 200

    data_id = response.get_json()["id"]
    assert isinstance(data_id, str) and len(data_id) > 0
    assert response.get_json()["geode_object_type"] == "PointSet3D"
    assert response.get_json()["viewable_file"].endswith(".vtp")

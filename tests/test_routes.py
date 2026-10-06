# Standard library imports
import os

# Third party imports
import opengeode as og
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
from opengeodeweb_back.routes.blueprint_routes import extract_valid_attribute_values
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

base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"
DUMMY_GEODE_ID = "00000000-0000-0000-0000-000000000000"


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
    file = data_dir / filename
    print(f"{file=}", flush=True)
    response = client.put(
        f"/opengeodeweb_back/upload_file",
        data={"file": FileStorage(file.open("rb"))},
    )
    assert response.status_code == 201


def test_upload_file_raw(client: FlaskClient, filename: str = "test.og_brep") -> None:
    file_bytes = (data_dir / filename).read_bytes()

    raw_filename = "raw_upload_test.og_brep"
    response = client.put(
        f"/opengeodeweb_back/upload_file?filename={raw_filename}",
        data=file_bytes,
        content_type="application/octet-stream",
    )
    assert response.status_code == 201

    uploaded_path = data_dir / raw_filename
    try:
        assert uploaded_path.read_bytes() == file_bytes
    finally:
        uploaded_path.unlink()


def test_upload_file_raw_missing_filename(client: FlaskClient) -> None:
    response = client.put(
        f"/opengeodeweb_back/upload_file",
        data=b"some raw bytes",
        content_type="application/octet-stream",
    )
    assert response.status_code == 400


def test_upload_file_chunked(client: FlaskClient, filename: str = "test.og_brep") -> None:
    file_bytes = (data_dir / filename).read_bytes()

    chunk_filename = "chunked_upload_test.og_brep"
    chunk_size = max(1, len(file_bytes) // 3)
    chunks = [
        file_bytes[index : index + chunk_size] for index in range(0, len(file_bytes), chunk_size)
    ]
    total_chunks = len(chunks)

    uploaded_path = data_dir / chunk_filename
    try:
        for chunk_index, chunk in enumerate(chunks):
            response = client.put(
                f"/opengeodeweb_back/upload_file"
                f"?filename={chunk_filename}"
                f"&chunk_index={chunk_index}"
                f"&total_chunks={total_chunks}",
                data=chunk,
                content_type="application/octet-stream",
            )
            if chunk_index < total_chunks - 1:
                assert response.status_code == 200
                assert not uploaded_path.exists()
            else:
                assert response.status_code == 201

        assert uploaded_path.read_bytes() == file_bytes
    finally:
        uploaded_path.unlink(missing_ok=True)
        uploaded_path.with_name(f"{uploaded_path.name}.part").unlink(missing_ok=True)


def test_upload_file_chunked_invalid_chunk_index(client: FlaskClient) -> None:
    response = client.put(
        "/opengeodeweb_back/upload_file"
        "?filename=invalid_chunk_index.og_brep"
        "&chunk_index=2"
        "&total_chunks=2",
        data=b"some raw bytes",
        content_type="application/octet-stream",
    )
    assert response.status_code == 400


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


def test_validate_object(client: FlaskClient) -> None:
    response_save = test_save_viewable_file(client, "BRep", "cube.og_brep")
    assert response_save.status_code == 200
    model_id = response_save.get_json()["id"]
    response = client.post("/opengeodeweb_back/validate", json={"id": model_id})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["is_valid"] is True
    assert json_data["nb_issues"] == 0
    assert type(json_data["issues"]) is list


def test_validate_invalid_object(client: FlaskClient) -> None:
    response_save = test_save_viewable_file(client, "BRep", "wrong_boundary_surface_model.og_brep")
    assert response_save.status_code == 200
    model_id = response_save.get_json()["id"]
    response = client.post("/opengeodeweb_back/validate", json={"id": model_id})
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data["is_valid"] is False
    assert json_data["nb_issues"] == 1
    assert type(json_data["issues"]) is list


def test_geode_objects_and_output_extensions(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/geode_objects_and_output_extensions"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
            "filename": "corbi.og_brep",
        }

    response = client.post(route, json=get_full_data())

    assert response.status_code == 200
    geode_objects_and_output_extensions = response.get_json()["geode_objects_and_output_extensions"]
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
        file = str(data_dir / "hat.vtp")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post("/opengeodeweb_back/texture_coordinates", json={"id": data.id})
    assert response.status_code == 200
    texture_coordinates = response.get_json()["texture_coordinates"]
    assert type(texture_coordinates) is list
    for texture_coordinate in texture_coordinates:
        assert type(texture_coordinate) is str


def test_vertex_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/vertex_attribute_names"

    with client.application.app_context():
        file = str(data_dir / "test.vtp")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)
    print(
        f"[ATTRIBUTES]: ",
        [attribute["nb_items"] for attribute in attributes],
        flush=True,
    )


def test_cell_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/cell_attribute_names"

    with client.application.app_context():
        file = str(data_dir / "test.og_rgd2d")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodeRegularGrid2D.geode_object_type(),
            viewer_object=GeodeRegularGrid2D.viewer_type(),
            viewer_elements_type=GeodeRegularGrid2D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)
    print(
        f"[ATTRIBUTES]: ",
        [attribute["nb_items"] for attribute in attributes],
        flush=True,
    )


def test_polygon_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polygon_attribute_names"

    with client.application.app_context():
        file = str(data_dir / "test.vtp")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodePolygonalSurface3D.geode_object_type(),
            viewer_object=GeodePolygonalSurface3D.viewer_type(),
            viewer_elements_type=GeodePolygonalSurface3D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)
    print(
        f"[ATTRIBUTES]: ",
        [attribute["nb_items"] for attribute in attributes],
        flush=True,
    )


def test_polyhedron_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/polyhedron_attribute_names"

    with client.application.app_context():
        file = str(data_dir / "test.vtu")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodePolyhedralSolid3D.geode_object_type(),
            viewer_object=GeodePolyhedralSolid3D.viewer_type(),
            viewer_elements_type=GeodePolyhedralSolid3D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    print(response.get_json())
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)
        if attribute["attribute_name"] == "Range":
            assert attribute["min_value"] == 0.0
            assert attribute["max_value"] == 579.0
    print(
        f"[ATTRIBUTES]: ",
        [attribute["nb_items"] for attribute in attributes],
        flush=True,
    )


def test_edge_attribute_names(client: FlaskClient, test_id: str) -> None:
    route = f"/opengeodeweb_back/edge_attribute_names"

    with client.application.app_context():
        file = str(data_dir / "test.og_edc3d")
        data = Data.create(
            geode_id=DUMMY_GEODE_ID,
            geode_object=GeodeEdgedCurve3D.geode_object_type(),
            viewer_object=GeodeEdgedCurve3D.viewer_type(),
            viewer_elements_type=GeodeEdgedCurve3D.viewer_elements_type(),
        )
        data.native_file = file
        session = get_session()
        if session:
            session.commit()

        data_path = Path(geode_functions.data_file_path(data.id, data.native_file))
        data_path.parent.mkdir(parents=True, exist_ok=True)
        assert data_path.exists(), f"File not found at {data_path}"
    response = client.post(route, json={"id": data.id})
    print(response.get_json())
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    print(f"[ATTRIBUTES]: ", attributes, flush=True)
    assert type(attributes) is list
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)
    print(
        f"[ATTRIBUTES]: ",
        [attribute["nb_items"] for attribute in attributes],
        flush=True,
    )


def test_database_uri_path(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        expected_db_path = (Path(app.config["DATA_FOLDER_PATH"]) / "project.db").resolve()
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri

        assert expected_db_path.exists()


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
    filename = "cube.og_brep"
    response = test_save_viewable_file(client, geode_object_type, filename)
    assert response.status_code == 200
    assert "mesh_components" in response.get_json()
    mesh_components = response.get_json()["mesh_components"]
    assert isinstance(mesh_components, list)
    assert len(mesh_components) > 0
    for mesh_component in mesh_components:
        assert isinstance(mesh_component, dict)
        assert isinstance(mesh_component["geode_id"], str)
        assert isinstance(mesh_component["viewer_id"], int)
        assert isinstance(mesh_component["name"], str)
        assert isinstance(mesh_component["type"], str)
        assert isinstance(mesh_component["boundaries"], list)
        for boundary_uuid in mesh_component["boundaries"]:
            assert isinstance(boundary_uuid, str)
        assert isinstance(mesh_component["internals"], list)
        for internal_uuid in mesh_component["internals"]:
            assert isinstance(internal_uuid, str)
        assert isinstance(mesh_component["is_active"], bool)
    assert "collection_components" in response.get_json()
    collection_components = response.get_json()["collection_components"]
    assert isinstance(collection_components, list)
    for collection_component in collection_components:
        assert isinstance(collection_component, dict)
        assert isinstance(collection_component["geode_id"], str)
        assert isinstance(collection_component["name"], str)
        assert isinstance(collection_component["items"], list)
        for item_uuid in collection_component["items"]:
            assert isinstance(item_uuid, str)
        assert isinstance(collection_component["is_active"], bool)


def test_export_project_route(client: FlaskClient, tmp_path: Path) -> None:
    route = "/opengeodeweb_back/export_project"
    snapshot = {"styles": {"1": {"visibility": True, "opacity": 1.0, "color": [0.2, 0.6, 0.9]}}}
    filename = "export_project_test.vease"
    project_folder = Path(client.application.config["DATA_FOLDER_PATH"])
    project_folder.mkdir(parents=True, exist_ok=True)
    assert (project_folder / "project.db").is_file()

    with get_session() as session:
        session.query(Data).delete()
        session.commit()

        data1 = Data(
            id="test_data_1",
            geode_id=DUMMY_GEODE_ID,
            geode_object="BRep",
            viewer_object="BRep",
            viewer_elements_type="default",
            native_file="native.txt",
        )
        data2 = Data(
            id="test_data_2",
            geode_id=DUMMY_GEODE_ID,
            geode_object="Section",
            viewer_object="Section",
            viewer_elements_type="default",
            native_file="native.txt",
        )
        session.add(data1)
        session.add(data2)
        session.commit()

        data1_dir = project_folder / "test_data_1"
        data1_dir.mkdir(parents=True, exist_ok=True)
        (data1_dir / "native.txt").write_text("native file content")

        data2_dir = project_folder / "test_data_2"
        data2_dir.mkdir(parents=True, exist_ok=True)
        (data2_dir / "native.txt").write_text("native file content")

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

    (project_folder / filename).unlink(missing_ok=True)


def test_import_project_route(client: FlaskClient, tmp_path: Path) -> None:
    route = "/opengeodeweb_back/import_project"
    snapshot = {"styles": {"1": {"visibility": True, "opacity": 1.0, "color": [0.2, 0.6, 0.9]}}}

    original_data_folder = client.application.config["DATA_FOLDER_PATH"]
    client.application.config["DATA_FOLDER_PATH"] = str(tmp_path / "project_data")
    db_path = tmp_path / "project_data" / "project.db"

    import sqlite3, zipfile, json

    temp_db = tmp_path / "temp_project.db"
    conn = sqlite3.connect(str(temp_db))
    conn.execute(
        "CREATE TABLE datas (id TEXT PRIMARY KEY, geode_id TEXT, geode_object TEXT, viewer_object TEXT, viewer_elements_type TEXT, native_file TEXT, "
        "viewable_file TEXT, light_viewable_file TEXT)"
    )
    conn.commit()
    conn.close()

    z = tmp_path / "import_project_test.vease"
    with zipfile.ZipFile(z, "w", compression=zipfile.ZIP_DEFLATED) as zipf:
        zipf.writestr("snapshot.json", json.dumps(snapshot))
        zipf.write(str(temp_db), "project.db")

    with z.open("rb") as f:
        resp = client.post(
            route,
            data={"file": (f, "import_project_test.vease")},
            content_type="multipart/form-data",
        )

    assert resp.status_code == 200
    assert resp.get_json().get("snapshot") == snapshot
    assert db_path.exists()

    from opengeodeweb_microservice.database import connection

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder
    test_db_path = os.environ.get("TEST_DB_PATH")
    if test_db_path:
        connection.init_database(test_db_path, create_tables=True)

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder


def test_save_viewable_workflow_from_object(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/create/point_set"
    point_data = {
        "name": "workflow_point_3d",
        "points": [{"x": 0.0, "y": 0.0, "z": 0.0}],
    }

    response = client.post(route, json=point_data)
    assert response.status_code == 200

    data_id = response.get_json()["id"]
    assert isinstance(data_id, str) and len(data_id) > 0
    assert response.get_json()["geode_object_type"] == "PointSet3D"
    assert response.get_json()["viewable_file"].endswith(".vtp")


def _load_brep_components(client: FlaskClient) -> tuple[str, dict[str, list[str]]]:
    """Load cube.og_brep and return (model_id, {component_type: [geode_id, ...]})."""
    response = test_save_viewable_file(client, "BRep", "cube.og_brep")
    assert response.status_code == 200
    model_id: str = response.get_json()["id"]
    mesh_components: list[dict[str, object]] = response.get_json()["mesh_components"]
    by_type: dict[str, list[str]] = {}
    for mesh_component in mesh_components:
        component_type = mesh_component["type"]
        geode_id = mesh_component["geode_id"]
        assert isinstance(component_type, str)
        assert isinstance(geode_id, str)
        by_type.setdefault(component_type, []).append(geode_id)
    return model_id, by_type


def _assert_attributes_response(response: TestResponse) -> None:
    assert response.status_code == 200
    attributes = response.get_json()["attributes"]
    assert isinstance(attributes, list)
    for attribute in attributes:
        assert "attribute_name" in attribute
        assert "min_value" in attribute
        assert "max_value" in attribute
        assert "nb_items" in attribute
        assert "min_values" in attribute
        assert "max_values" in attribute
        assert "no_data" in attribute
        assert isinstance(attribute["no_data"], bool)


def test_model_component_vertex_attribute_names(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/model_component_vertex_attribute_names"
    model_id, by_type = _load_brep_components(client)

    corner_ids = by_type.get("Corner", [])
    assert len(corner_ids) > 0, "cube.og_brep should have Corner components"

    response = client.post(route, json={"id": model_id, "component_ids": corner_ids})
    _assert_attributes_response(response)

    def get_full_data() -> test_utils.JsonData:
        return {"id": model_id, "component_ids": corner_ids}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_model_component_edge_attribute_names(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/model_component_edge_attribute_names"
    model_id, by_type = _load_brep_components(client)

    line_ids = by_type.get("Line", [])
    assert len(line_ids) > 0, "cube.og_brep should have Line components"

    response = client.post(route, json={"id": model_id, "component_ids": line_ids})
    _assert_attributes_response(response)

    def get_full_data() -> test_utils.JsonData:
        return {"id": model_id, "component_ids": line_ids}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_model_component_polygon_attribute_names(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/model_component_polygon_attribute_names"
    model_id, by_type = _load_brep_components(client)

    surface_ids = by_type.get("Surface", [])
    assert len(surface_ids) > 0, "cube.og_brep should have Surface components"

    response = client.post(route, json={"id": model_id, "component_ids": surface_ids})
    _assert_attributes_response(response)

    def get_full_data() -> test_utils.JsonData:
        return {"id": model_id, "component_ids": surface_ids}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_model_component_polyhedron_attribute_names(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/model_component_polyhedron_attribute_names"
    model_id, by_type = _load_brep_components(client)

    block_ids = by_type.get("Block", [])
    assert len(block_ids) > 0, "cube.og_brep should have Block components"

    response = client.post(route, json={"id": model_id, "component_ids": block_ids})
    _assert_attributes_response(response)

    def get_full_data() -> test_utils.JsonData:
        return {"id": model_id, "component_ids": block_ids}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_extract_valid_attribute_values_with_sentinel_no_value() -> None:
    mesh = og.TriangulatedSurface3D.create()
    builder = og.TriangulatedSurfaceBuilder3D.create(mesh)
    vertex_0 = builder.create_point(og.Point3D([0, 0, 0]))
    vertex_1 = builder.create_point(og.Point3D([1, 0, 0]))
    builder.create_triangle([vertex_0, vertex_1, vertex_0])

    attribute_manager = mesh.vertex_attribute_manager()
    values_config = og.AttributeValuesDouble()
    values_config.no_value = -999.0
    attribute_id = attribute_manager.create_attribute_variable_double(
        "variable_double", values_config, og.AttributeProperties()
    )
    attribute = attribute_manager.find_attribute_variable_double(attribute_id)
    attribute.set_value(vertex_0, -999.0)
    attribute.set_value(vertex_1, 42.0)

    valid_values, has_nan = extract_valid_attribute_values(attribute_manager, "variable_double", 0)
    assert has_nan is True
    assert valid_values == [42.0]


def test_extract_valid_attribute_values_with_non_transferable_attribute() -> None:
    mesh = og.TriangulatedSurface3D.create()
    builder = og.TriangulatedSurfaceBuilder3D.create(mesh)
    vertex_0 = builder.create_point(og.Point3D([0, 0, 0]))
    builder.create_triangle([vertex_0, vertex_0, vertex_0])

    attribute_manager = mesh.vertex_attribute_manager()
    properties = og.AttributeProperties()
    properties.transferable = False
    attribute_manager.create_attribute_variable_double(
        "internal_attribute", og.AttributeValuesDouble(), properties
    )

    valid_values, has_nan = extract_valid_attribute_values(
        attribute_manager, "internal_attribute", 0
    )
    assert has_nan is False
    assert valid_values == []


def test_data_id_length_is_strict(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/vertex_attribute_names"
    for wrong_id in ["a" * 31, "a" * 33, DUMMY_GEODE_ID]:
        response = client.post(route, json={"id": wrong_id})
        assert response.status_code == 400, wrong_id


def test_component_id_length_is_strict(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/model_component_vertex_attribute_names"
    model_id, _ = _load_brep_components(client)
    response = client.post(route, json={"id": model_id, "component_ids": ["a" * 32]})
    assert response.status_code == 400

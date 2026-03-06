import os
import shutil
import zipfile
import json
from flask.testing import FlaskClient
from werkzeug.datastructures import FileStorage
from pathlib import Path

from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_back import geode_functions
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep


from .test_routes import test_save_viewable_file

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_model_components(client: FlaskClient) -> None:
    geode_object_type = "BRep"
    filename = "cube.og_brep"
    response = test_save_viewable_file(client, geode_object_type, filename)

    route = "/opengeodeweb_back/models/model_components"
    brep_filename = os.path.join(data_dir, "cube.og_brep")

    response = client.post(route, json={"id": response.get_json()["id"]})
    assert response.status_code == 200
    assert "mesh_components" in response.get_json()
    mesh_components = response.get_json()["mesh_components"]
    assert isinstance(mesh_components, list)
    assert len(mesh_components) > 0
    for mesh_component in mesh_components:
        assert isinstance(mesh_component, object)
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

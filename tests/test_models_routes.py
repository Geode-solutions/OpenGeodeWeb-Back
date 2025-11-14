import os
import shutil

from opengeodeweb_back import geode_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from werkzeug.datastructures import FileStorage
import zipfile
import json

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_model_mesh_components(client, test_id):
    route = "/opengeodeweb_back/models/vtm_component_indices"

    with client.application.app_context():
        data_path = geode_functions.data_file_path(test_id, "viewable.vtm")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy(os.path.join(data_dir, "cube.vtm"), data_path)

    response = client.post(route, json={"id": test_id})
    assert response.status_code == 200

    uuid_dict = response.json["uuid_to_flat_index"]
    assert isinstance(uuid_dict, dict)

    indices = list(uuid_dict.values())
    indices.sort()
    assert all(indices[i] > indices[i - 1] for i in range(1, len(indices)))
    for uuid in uuid_dict.keys():
        assert isinstance(uuid, str)


def test_extract_brep_uuids(client, test_id):
    route = "/opengeodeweb_back/models/mesh_components"
    brep_filename = os.path.join(data_dir, "cube.og_brep")

    with client.application.app_context():
        data_entry = Data.create(
            geode_object="BRep",
            viewer_object=geode_functions.get_object_type("BRep"),
            input_file=brep_filename,
        )
        data_entry.native_file_name = brep_filename
        session = get_session()
        if session:
            session.commit()

        response = client.post(route, json={"id": data_entry.id})
        assert response.status_code == 200
        assert "uuid_dict" in response.json
        uuid_dict = response.json["uuid_dict"]
        assert isinstance(uuid_dict, dict)


def test_export_project_route(client, tmp_path):
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
    response.close()
    export_path = os.path.join(project_folder, filename)
    if os.path.exists(export_path):
        os.remove(export_path)


def test_import_project_route(client, tmp_path):
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
        "CREATE TABLE datas (id TEXT PRIMARY KEY, geode_object TEXT, viewer_object TEXT, native_file_name TEXT, "
        "viewable_file_name TEXT, light_viewable TEXT, input_file TEXT, additional_files TEXT)"
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
    assert resp.json.get("snapshot") == snapshot
    assert os.path.exists(db_path)

    from opengeodeweb_microservice.database import connection

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder
    test_db_path = os.environ.get("TEST_DB_PATH")
    if test_db_path:
        connection.init_database(test_db_path, create_tables=True)

    client.application.config["DATA_FOLDER_PATH"] = original_data_folder


def test_save_viewable_workflow_from_file(client):
    file = os.path.join(data_dir, "cube.og_brep")
    upload_resp = client.put(
        "/opengeodeweb_back/upload_file",
        data={"file": FileStorage(open(file, "rb"))},
    )
    assert upload_resp.status_code == 201

    route = "/opengeodeweb_back/save_viewable_file"
    payload = {"input_geode_object": "BRep", "filename": "cube.og_brep"}

    response = client.post(route, json=payload)
    assert response.status_code == 200

    data_id = response.json["id"]
    assert isinstance(data_id, str) and len(data_id) > 0
    assert response.json["viewable_file_name"].endswith(".vtm")

    comp_resp = client.post(
        "/opengeodeweb_back/models/vtm_component_indices", json={"id": data_id}
    )
    assert comp_resp.status_code == 200

    refreshed = Data.get(data_id)
    assert refreshed is not None


def test_save_viewable_workflow_from_object(client):
    route = "/opengeodeweb_back/create/create_aoi"
    aoi_data = {
        "name": "workflow_aoi",
        "points": [
            {"x": 0.0, "y": 0.0},
            {"x": 1.0, "y": 0.0},
            {"x": 1.0, "y": 1.0},
            {"x": 0.0, "y": 1.0},
        ],
        "z": 0.0,
    }

    response = client.post(route, json=aoi_data)
    assert response.status_code == 200

    data_id = response.json["id"]
    assert isinstance(data_id, str) and len(data_id) > 0
    assert response.json["geode_object"] == "EdgedCurve3D"
    assert response.json["viewable_file_name"].endswith(".vtp")

    attr_resp = client.post(
        "/opengeodeweb_back/vertex_attribute_names", json={"id": data_id}
    )
    assert attr_resp.status_code == 200
    assert isinstance(attr_resp.json.get("vertex_attribute_names", []), list)

import os
import shutil
import flask

from opengeodeweb_back import geode_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
import zipfile
import json
import io


def test_model_mesh_components(client, test_id):
    route = "/opengeodeweb_back/models/vtm_component_indices"

    with client.application.app_context():
        data_path = geode_functions.data_file_path(test_id, "viewable.vtm")
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy("./tests/data/cube.vtm", data_path)

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
    brep_filename = "cube.og_brep"

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

        src_path = os.path.join("tests", "data", brep_filename)
        dest_path = os.path.join(
            flask.current_app.config["DATA_FOLDER_PATH"], data_entry.id, brep_filename
        )
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(src_path, dest_path)

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
    filename = "export_project_test.zip"
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

    client.application.config["DATA_FOLDER_PATH"] = os.path.join(
        str(tmp_path), "project_data"
    )
    data_folder = client.application.config["DATA_FOLDER_PATH"]
    pre_existing_db_path = os.path.join(data_folder, "project.db")

    tmp_zip = tmp_path / "import_project_test.zip"
    new_database_bytes = b"new_db_content"
    with zipfile.ZipFile(tmp_zip, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("snapshot.json", json.dumps(snapshot))
        zip_file.writestr("project.db", new_database_bytes)

    with open(tmp_zip, "rb") as file:
        response = client.post(
            route,
            data={"file": (file, "import_project_test.zip")},
            content_type="multipart/form-data",
        )

    assert response.status_code == 200
    assert response.json.get("snapshot") == snapshot

    assert os.path.exists(pre_existing_db_path)
    with open(pre_existing_db_path, "rb") as file:
        assert file.read() == new_database_bytes

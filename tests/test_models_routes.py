import os
import shutil
import flask

from opengeodeweb_back import geode_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session


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

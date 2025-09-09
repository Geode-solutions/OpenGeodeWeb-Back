import os
import shutil
import flask

from src.opengeodeweb_back import geode_functions
from src.opengeodeweb_back.data import Data
from src.opengeodeweb_back.database import database


def test_model_mesh_components(client, test_id):
    route = f"/models/vtm_component_indices"

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
    route = "/models/mesh_components"
    brep_filename = "cube.og_brep"

    with client.application.app_context():
        data_entry = Data.create(geode_object="BRep", input_file=brep_filename)
        data_entry.native_file_name = brep_filename
        database.session.commit()

        data_path = geode_functions.data_file_path(data_entry.id, brep_filename)
        os.makedirs(os.path.dirname(data_path), exist_ok=True)
        shutil.copy(f"./tests/data/{brep_filename}", data_path)

    json_data = {"id": data_entry.id}
    response = client.post(route, json=json_data)

    assert response.status_code == 200
    uuid_dict = response.json["uuid_dict"]
    assert isinstance(uuid_dict, dict)
    expected_keys = {"Block", "Line", "Surface", "Corner"}
    assert any(key in uuid_dict for key in expected_keys)
    for key, value in uuid_dict.items():
        assert isinstance(value, list)
        assert all(isinstance(v, str) for v in value)

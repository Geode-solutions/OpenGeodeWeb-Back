import os
import shutil

from src.opengeodeweb_back import geode_functions

def test_model_mesh_components(client, test_id):
    route = "/models/vtm_component_indices"

    data_path = geode_functions.data_file_path(
        {"id": test_id},
        "viewable.vtm"
    )
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    shutil.copy("./tests/data/cube.vtm", data_path)

    response = client.post(route, json={"id": test_id})
    assert response.status_code == 200

    uuid_dict = response.json["uuid_to_flat_index"]
    assert isinstance(uuid_dict, dict)

    indices = sorted(uuid_dict.values())
    assert all(indices[i] > indices[i - 1] for i in range(1, len(indices)))
    for key in uuid_dict:
        assert isinstance(key, str)


def test_extract_brep_uuids(client, test_id):
    route = "/models/mesh_components"

    brep_filename = "cube.og_brep"
    json_data = {"id": test_id, "geode_object": "BRep", "filename": brep_filename}

    data_path = geode_functions.data_file_path(
        json_data,
        brep_filename
    )
    os.makedirs(os.path.dirname(data_path), exist_ok=True)
    shutil.copy(f"./tests/data/{brep_filename}", data_path)

    response = client.post(route, json=json_data)
    assert response.status_code == 200

    uuid_dict = response.json["uuid_dict"]
    assert isinstance(uuid_dict, dict)
    expected = {"Block", "Line", "Surface", "Corner"}
    assert any(k in uuid_dict for k in expected)
    for values in uuid_dict.values():
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)

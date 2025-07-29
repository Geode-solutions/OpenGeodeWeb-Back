import os
import shutil


def test_model_mesh_components(client):
    test_id = "1"
    route = "/models/vtm_component_indices"

    base_path = client.application.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(base_path, test_id)
    os.makedirs(data_path, exist_ok=True)
    shutil.copy("./tests/data/cube.vtm", os.path.join(data_path, "viewable.vtm"))

    response = client.post(route, json={"id": test_id})
    assert response.status_code == 200

    uuid_dict = response.json["uuid_to_flat_index"]
    assert isinstance(uuid_dict, dict)

    indices = sorted(uuid_dict.values())
    assert all(indices[i] > indices[i - 1] for i in range(1, len(indices)))
    for key in uuid_dict:
        assert isinstance(key, str)


def test_extract_brep_uuids(client):
    test_id = "1"
    route = "/models/mesh_components"

    base_path = client.application.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(base_path, test_id)
    os.makedirs(data_path, exist_ok=True)
    shutil.copy("./tests/data/cube.og_brep", os.path.join(data_path, "cube.og_brep"))

    json_data = {"id": test_id, "geode_object": "BRep", "filename": "cube.og_brep"}
    response = client.post(route, json=json_data)
    assert response.status_code == 200

    uuid_dict = response.json["uuid_dict"]
    assert isinstance(uuid_dict, dict)
    expected = {"Block", "Line", "Surface", "Corner"}
    assert any(k in uuid_dict for k in expected)
    for values in uuid_dict.values():
        assert isinstance(values, list)
        assert all(isinstance(v, str) for v in values)

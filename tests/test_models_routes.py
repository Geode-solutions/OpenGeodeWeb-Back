import shutil
import os


def test_model_mesh_components(client, uuid_project_structure):
    route = "/models/vtm_component_indices"
    uuid_data = uuid_project_structure["uuid_data"]
    data_path = uuid_project_structure["data_path"]

    shutil.copy("./tests/data/cube.vtm", os.path.join(data_path, "viewable.vtm"))

    original_path = client.application.config["DATA_FOLDER_PATH"]
    client.application.config["DATA_FOLDER_PATH"] = uuid_project_structure["base_path"]

    try:
        response = client.post(route, json={"id": uuid_data})
        assert response.status_code == 200
        uuid_dict = response.json["uuid_to_flat_index"]
        assert isinstance(uuid_dict, dict)

        indices = list(uuid_dict.values())
        indices.sort()
        assert all(indices[i] > indices[i - 1] for i in range(1, len(indices)))
        for uuid_key in uuid_dict.keys():
            assert isinstance(uuid_key, str)
    finally:
        client.application.config["DATA_FOLDER_PATH"] = original_path


def test_extract_brep_uuids(client, uuid_project_structure):
    route = "/models/mesh_components"
    uuid_data = uuid_project_structure["uuid_data"]
    data_path = uuid_project_structure["data_path"]

    shutil.copy("./tests/data/cube.og_brep", os.path.join(data_path, "cube.og_brep"))

    original_path = client.application.config["DATA_FOLDER_PATH"]
    client.application.config["DATA_FOLDER_PATH"] = uuid_project_structure["base_path"]

    try:
        json_data = {
            "filename": "cube.og_brep",
            "geode_object": "BRep",
            "id": uuid_data,
        }
        response = client.post(route, json=json_data)
        assert response.status_code == 200

        uuid_dict = response.json["uuid_dict"]
        assert isinstance(uuid_dict, dict)
        expected_keys = {"Block", "Line", "Surface", "Corner"}
        assert any(key in uuid_dict for key in expected_keys)
        for key, value in uuid_dict.items():
            assert isinstance(value, list)
            assert all(isinstance(v, str) for v in value)
    finally:
        client.application.config["DATA_FOLDER_PATH"] = original_path

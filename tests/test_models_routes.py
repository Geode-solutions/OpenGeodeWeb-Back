def test_model_mesh_components(client):
    route = f"/models/vtm_component_indices"
    get_full_data = lambda: {"id": "cube"}
    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200

    uuid_dict = response.json["uuid_to_flat_index"]
    assert isinstance(uuid_dict, dict)

    indices = list(uuid_dict.values())
    indices.sort()
    assert all(indices[i] > indices[i - 1] for i in range(1, len(indices)))
    for uuid in uuid_dict.keys():
        assert isinstance(uuid, str)


def test_extract_brep_uuids(client):
    route = "/models/mesh_components"
    json_data = {"filename": "cube.og_brep", "geode_object": "BRep"}
    response = client.post(route, json=json_data)

    assert response.status_code == 200
    uuid_dict = response.json["uuid_dict"]
    assert isinstance(uuid_dict, dict)
    expected_keys = {"Block", "Line", "Surface", "Corner"}
    assert any(key in uuid_dict for key in expected_keys)
    for key, value in uuid_dict.items():
        assert isinstance(value, list)
        assert all(isinstance(v, str) for v in value)

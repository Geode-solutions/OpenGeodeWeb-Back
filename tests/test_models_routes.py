def test_model_mesh_components(client):
    route = f"/models/vtm_component_indices"
    get_full_data = lambda: {"id": "cube"}
    json = get_full_data()
    response = client.post(route, json=json)
    assert response.status_code == 200
    uuid_dict = response.json["uuid_to_flat_index"]
    assert type(uuid_dict) is dict

    indices = list(uuid_dict.values())
    indices.sort()
    assert indices[0] == 1
    assert all(indices[i] == indices[i - 1] + 1 for i in range(1, len(indices)))


def test_extract_brep_uuids(client):
    route = "/models/mesh_components"
    json_data = {"filename": "cube.og_brep", "geode_object": "BRep"}

    response = client.post(route, json=json_data)

    assert response.status_code == 200
    uuid_dict = response.json["uuid_dict"]
    assert isinstance(uuid_dict, dict)
    assert (
        "Block" in uuid_dict
        or "Line" in uuid_dict
        or "Surface" in uuid_dict
        or "Corner" in uuid_dict
    )

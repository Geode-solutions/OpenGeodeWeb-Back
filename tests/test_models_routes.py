import os

from werkzeug.datastructures import FileStorage

from src.opengeodeweb_back import geode_functions, geode_objects, test_utils


def test_model_components(client):
    route = f"/models/components"
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

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)

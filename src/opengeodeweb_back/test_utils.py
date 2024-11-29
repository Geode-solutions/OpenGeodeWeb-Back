# Standard library imports

# Third party imports

# Local application imports


def test_route_wrong_params(client, route, get_full_data):
    for key, value in get_full_data().items():
        json = get_full_data()
        json.pop(key)
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.json["description"]
        assert error_description == f"Validation error: '{key}' is a required property"

    json = get_full_data()
    json["dumb_key"] = "dumb_value"
    response = client.post(route, json=json)
    assert response.status_code == 400
    error_description = response.json["description"]
    assert (
        error_description
        == "Validation error: Additional properties are not allowed ('dumb_key' was unexpected)"
    )

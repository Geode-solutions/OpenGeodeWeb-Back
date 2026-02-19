# Standard library imports
from typing import Callable, Any

# Third party imports
from flask.testing import FlaskClient

# Local application imports

JsonData = dict[str, Any]


def test_route_wrong_params(
    client: FlaskClient, route: str, get_full_data: Callable[[], JsonData], path: list = []
) -> None:
    def get_json():
        json = get_full_data()
        target = json
        for p in path:
            target = target[p]
        return json, target

    data = get_json()[1]
    if isinstance(data, dict):
        for key, value in data.items():
            json, target = get_json()
            target.pop(key)
            response = client.post(route, json=json)
            if response.status_code == 400:
                error_description = response.get_json()["description"]
                assert "must contain" in error_description
                assert f"'{key}'" in error_description
            if isinstance(value, (dict, list)):
                test_route_wrong_params(client, route, get_full_data, path + [key])

        json, target = get_json()
        target["dumb_key"] = "dumb_value"
        response = client.post(route, json=json)
        assert response.status_code == 400
        error_description = response.get_json()["description"]
        assert "must not contain" in error_description
        assert "'dumb_key'" in error_description
    elif isinstance(data, list) and data:
        test_route_wrong_params(client, route, get_full_data, path + [0])

from __future__ import annotations

# Standard library imports
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third party imports
from werkzeug.datastructures import FileStorage

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask.testing import FlaskClient
    from werkzeug.test import TestResponse

# Local application imports

JsonData = dict[str, Any]


def _check(condition: bool, message: str) -> None:  # noqa: FBT001
    # Explicit raise instead of assert: this module is not rewritten by pytest
    # and asserts are stripped when Python runs with -O.
    if not condition:
        raise AssertionError(message)


def test_route_wrong_params(
    client: FlaskClient,
    route: str,
    get_full_data: Callable[[], JsonData],
) -> None:
    _check_wrong_params_at(client, route, get_full_data, [])


def _check_wrong_params_at(
    client: FlaskClient,
    route: str,
    get_full_data: Callable[[], JsonData],
    path: list[str | int],
) -> None:
    def get_json() -> tuple[JsonData, Any]:
        json = get_full_data()
        target: Any = json
        for sub_path in path:
            target = target[sub_path]
        return json, target

    data = get_json()[1]
    if isinstance(data, dict):
        for key, value in data.items():
            json, target = get_json()
            target.pop(key)
            response = client.post(route, json=json)
            if response.status_code == HTTPStatus.BAD_REQUEST:
                error_description: str = response.get_json()["description"]
                _check(
                    "must contain" in error_description and f"'{key}'" in error_description,
                    f"{route}: missing '{key}' gave unexpected error: {error_description}",
                )
            if isinstance(value, (dict, list)):
                _check_wrong_params_at(client, route, get_full_data, [*path, key])

        json, target = get_json()
        target["dumb_key"] = "dumb_value"
        response = client.post(route, json=json)
        _check(
            response.status_code == HTTPStatus.BAD_REQUEST,
            f"{route}: extra 'dumb_key' gave status {response.status_code}, expected 400",
        )
        error_description = response.get_json()["description"]
        _check(
            "must not contain" in error_description and "'dumb_key'" in error_description,
            f"{route}: extra 'dumb_key' gave unexpected error: {error_description}",
        )
    elif isinstance(data, list) and data:
        _check_wrong_params_at(client, route, get_full_data, [*path, 0])


def check_upload_file(client: FlaskClient, filename: str) -> None:
    # Test data lives in the "data" folder of the tests' project folder
    file = Path(client.application.config["PROJECT_FOLDER_PATH"]) / "data" / filename
    response = client.put(
        "/opengeodeweb_back/upload_file",
        data={"file": FileStorage(file.open("rb"))},
    )
    _check(response.status_code == HTTPStatus.CREATED, f"Upload of {filename} failed")


def check_save_viewable_file(
    client: FlaskClient,
    geode_object_type: str,
    filename: str,
) -> TestResponse:
    check_upload_file(client, filename)
    route = "/opengeodeweb_back/save_viewable_file"

    def get_full_data() -> JsonData:
        return {
            "geode_object_type": geode_object_type,
            "filename": filename,
        }

    response = client.post(route, json=get_full_data())
    _check(response.status_code == HTTPStatus.OK, f"Saving {filename} failed")
    json = response.get_json()
    _check(type(json["native_file"]) is str, "native_file is not a string")
    _check(type(json["viewable_file"]) is str, "viewable_file is not a string")
    _check(type(json.get("id")) is str, "id is not a string")
    _check(json["viewer_type"] in ["model", "mesh"], "viewer_type is not model or mesh")
    _check(type(json["binary_light_viewable"]) is str, "binary_light_viewable is not a string")

    # Test all params
    test_route_wrong_params(client, route, get_full_data)
    return response

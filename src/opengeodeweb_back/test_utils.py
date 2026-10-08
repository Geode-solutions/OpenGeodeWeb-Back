from __future__ import annotations

# Standard library imports
from http import HTTPStatus
from typing import TYPE_CHECKING, Any

# Third party imports

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask.testing import FlaskClient

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

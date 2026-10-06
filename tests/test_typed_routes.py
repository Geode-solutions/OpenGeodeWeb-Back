from __future__ import annotations

# Standard library imports
import json
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import fastjsonschema  # type: ignore[import-untyped]
from opengeodeweb_microservice.schemas import ERROR_SCHEMA_PATH

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.typed_route import TYPED_ROUTE_MARKER
from tests.conftest import app

if TYPE_CHECKING:
    import pytest
    from flask.testing import FlaskClient

BLUEPRINTS = ("opengeodeweb_back", "opengeodeweb_create")


with Path(ERROR_SCHEMA_PATH).open() as file:
    validate_error = fastjsonschema.compile(json.load(file))


def test_every_route_is_typed() -> None:
    for endpoint, view in app.view_functions.items():
        if endpoint.split(".")[0] not in BLUEPRINTS:
            continue
        assert getattr(view, TYPED_ROUTE_MARKER, False), (
            f"{endpoint} must be registered with @typed_route or @raw_route"
        )


def test_bad_params_error_response(client: FlaskClient) -> None:
    response = client.post("/opengeodeweb_back/allowed_objects", json={})
    assert response.status_code == 400
    validate_error(response.get_json())


def test_http_exception_error_response(client: FlaskClient) -> None:
    response = client.post("/error")
    assert response.status_code == 500
    validate_error(response.get_json())


def test_unexpected_exception_error_response(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail(_filename: str) -> str:
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(geode_functions, "upload_file_path", fail)
    response = client.post("/opengeodeweb_back/allowed_objects", json={"filename": "corbi.og_brep"})
    assert response.status_code == 500
    error = response.get_json()
    validate_error(error)
    assert error["description"] == "unexpected failure"

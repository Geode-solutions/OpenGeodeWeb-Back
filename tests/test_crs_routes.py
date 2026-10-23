from __future__ import annotations

# Standard library imports
import os
import shutil
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import pytest

# Local application imports
from opengeodeweb_microservice.database.data import Data

from opengeodeweb_back import crs_functions, geode_functions, test_utils
from opengeodeweb_back.geode_objects.geode_point_set3d import GeodePointSet3D

if TYPE_CHECKING:
    from flask.testing import FlaskClient

LAMBERT = {"authority": "EPSG", "code": "2154", "name": "RGF93 v1 / Lambert-93"}
UTM = {"authority": "EPSG", "code": "32631", "name": "WGS 84 / UTM zone 31N"}


def test_geographic_list(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/geographic_list"

    def get_full_data() -> test_utils.JsonData:
        return {
            "geode_object_type": "BRep",
        }

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    crs_list = response.get_json()["crs_list"]
    assert type(crs_list) is list
    for crs in crs_list:
        assert type(crs) is dict

    # Test all params
    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_active(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/active"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]

    def get_full_data() -> test_utils.JsonData:
        return {"id": point_set_id}

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    assert response.get_json()["crs_name"] == "points"
    assert "crs_info" not in response.get_json()

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_assign_geographic(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/assign_geographic"
    active_route = "/opengeodeweb_back/crs/active"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]

    def get_full_data() -> test_utils.JsonData:
        return {"id": point_set_id, **LAMBERT}

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    assert response.get_json()["crs"] == LAMBERT
    response = client.post(route, json={"id": point_set_id, **UTM})
    assert response.status_code == 200
    response = client.post(active_route, json={"id": point_set_id})
    assert response.get_json() == {"crs_name": "EPSG:32631", "crs_info": UTM}

    brep_id = test_utils.check_save_viewable_file(client, "BRep", "cube.og_brep").get_json()["id"]
    response = client.post(route, json={"id": brep_id, **LAMBERT})
    assert response.status_code == 200
    response = client.post(active_route, json={"id": brep_id})
    assert response.get_json() == {"crs_name": "EPSG:2154", "crs_info": LAMBERT}

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_crs_errors(client: FlaskClient) -> None:
    active_route = "/opengeodeweb_back/crs/active"
    assign_route = "/opengeodeweb_back/crs/assign_geographic"

    response = client.post(active_route, json={"id": "0" * 32})
    assert response.status_code == 404
    response = client.post(assign_route, json={"id": "0" * 32, **LAMBERT})
    assert response.status_code == 404

    grid_id = test_utils.check_save_viewable_file(
        client, "LightRegularGrid3D", "test.og_lrgd3d"
    ).get_json()["id"]
    response = client.post(active_route, json={"id": grid_id})
    assert response.status_code == 400
    response = client.post(assign_route, json={"id": grid_id, **LAMBERT})
    assert response.status_code == 400


def _first_point(client: FlaskClient, data_id: str) -> list[float]:
    with client.application.app_context():
        geode_object = geode_functions.load_geode_object(data_id)
    assert isinstance(geode_object, GeodePointSet3D)
    point = geode_object.point_set.point(0)
    return [point.value(0), point.value(1), point.value(2)]


def test_convert_geographic(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/convert_geographic"
    assign_route = "/opengeodeweb_back/crs/assign_geographic"
    active_route = "/opengeodeweb_back/crs/active"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    client.post(assign_route, json={"id": point_set_id, **LAMBERT})
    lambert_point = _first_point(client, point_set_id)

    def get_full_data() -> test_utils.JsonData:
        return {"id": point_set_id, **UTM}

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    # The front rebuilds its local actor from the new light viewable
    assert type(response.get_json()["binary_light_viewable"]) is str
    assert response.get_json()["crs"] == UTM
    response = client.post(active_route, json={"id": point_set_id})
    assert response.get_json() == {"crs_name": "EPSG:32631", "crs_info": UTM}
    assert _first_point(client, point_set_id) != lambert_point

    response = client.post(route, json={"id": point_set_id, **LAMBERT})
    assert response.status_code == 200
    response = client.post(active_route, json={"id": point_set_id})
    assert response.get_json()["crs_name"] == "EPSG:2154"
    assert _first_point(client, point_set_id) == pytest.approx(lambert_point, abs=1e-6)

    brep_id = test_utils.check_save_viewable_file(client, "BRep", "cube.og_brep").get_json()["id"]
    client.post(assign_route, json={"id": brep_id, **LAMBERT})
    response = client.post(route, json={"id": brep_id, **UTM})
    assert response.status_code == 200
    response = client.post(active_route, json={"id": brep_id})
    assert response.get_json()["crs_name"] == "EPSG:32631"

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_convert_geographic_errors(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/convert_geographic"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]

    response = client.post(route, json={"id": point_set_id, **UTM})
    assert response.status_code == 400

    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **UTM})
    response = client.post(route, json={"id": point_set_id, **UTM})
    assert response.status_code == 400

    response = client.post(route, json={"id": "0" * 32, **UTM})
    assert response.status_code == 404


SOURCE = [{"x": 0, "y": 0}, {"x": 10, "y": 0}, {"x": 0, "y": 10}]
TARGET = [{"x": 1000, "y": 2000}, {"x": 1000, "y": 2020}, {"x": 980, "y": 2000}]


def _create_point_set(client: FlaskClient) -> str:
    points = [
        {"x": 0, "y": 0, "z": 5},
        {"x": 10, "y": 0, "z": 5},
        {"x": 0, "y": 10, "z": 5},
    ]
    response = client.post(
        "/opengeodeweb_back/create/point_set", json={"name": "align", "points": points}
    )
    assert response.status_code == 200
    data_id: str = response.get_json()["id"]
    return data_id


def test_align(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/align"
    point_set_id = _create_point_set(client)

    def get_full_data() -> test_utils.JsonData:
        # Copies: test_route_wrong_params mutates the returned points
        return {
            "id": point_set_id,
            "source_points": [dict(point) for point in SOURCE],
            "target_points": [dict(point) for point in TARGET],
            **LAMBERT,
        }

    response = client.post(route, json=get_full_data())
    assert response.status_code == 200
    assert type(response.get_json()["binary_light_viewable"]) is str
    assert response.get_json()["crs"] == LAMBERT
    response = client.post("/opengeodeweb_back/crs/active", json={"id": point_set_id})
    assert response.get_json() == {"crs_name": "EPSG:2154", "crs_info": LAMBERT}
    assert _first_point(client, point_set_id) == [1000, 2000, 5]

    brep_id = test_utils.check_save_viewable_file(client, "BRep", "cube.og_brep").get_json()["id"]
    response = client.post(route, json={**get_full_data(), "id": brep_id})
    assert response.status_code == 200

    test_utils.test_route_wrong_params(client, route, get_full_data)


def test_align_errors(client: FlaskClient) -> None:
    route = "/opengeodeweb_back/crs/align"
    point_set_id = _create_point_set(client)
    colinear = [{"x": 0, "y": 0}, {"x": 1, "y": 1}, {"x": 2, "y": 2}]

    response = client.post(
        route,
        json={"id": point_set_id, "source_points": colinear, "target_points": TARGET, **LAMBERT},
    )
    assert response.status_code == 400

    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **LAMBERT})
    response = client.post(
        route,
        json={"id": point_set_id, "source_points": SOURCE, "target_points": TARGET, **LAMBERT},
    )
    assert response.status_code == 400


WGS84 = {"authority": "EPSG", "code": "4326", "name": "WGS 84"}
PSEUDO_MERCATOR = {"authority": "EPSG", "code": "3857", "name": "WGS 84 / Pseudo-Mercator"}


def test_reassign_after_convert(client: FlaskClient) -> None:
    assign_route = "/opengeodeweb_back/crs/assign_geographic"
    convert_route = "/opengeodeweb_back/crs/convert_geographic"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    client.post(assign_route, json={"id": point_set_id, **LAMBERT})
    client.post(convert_route, json={"id": point_set_id, **UTM})
    stale_utm_point = _first_point(client, point_set_id)

    # EPSG:2154 is still registered (inactive) after the conversion
    response = client.post(assign_route, json={"id": point_set_id, **LAMBERT})
    assert response.status_code == 200
    response = client.post(assign_route, json={"id": point_set_id, **LAMBERT})
    assert response.status_code == 400

    # Relabelling then converting must reproject, not reactivate the stale EPSG:32631
    client.post(assign_route, json={"id": point_set_id, **PSEUDO_MERCATOR})
    response = client.post(convert_route, json={"id": point_set_id, **UTM})
    assert response.status_code == 200
    assert _first_point(client, point_set_id) != pytest.approx(stale_utm_point)


def test_convert_out_of_domain(client: FlaskClient) -> None:
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    convert_route = "/opengeodeweb_back/crs/convert_geographic"
    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **LAMBERT})
    client.post(convert_route, json={"id": point_set_id, **UTM})
    # UTM metres read as degrees give an invalid latitude
    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **WGS84})
    response = client.post(convert_route, json={"id": point_set_id, **LAMBERT})
    assert response.status_code == 400


def test_saved_native_file_keeps_its_crs(client: FlaskClient) -> None:
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **LAMBERT})
    with client.application.app_context():
        data = Data.get(point_set_id)
        assert data is not None
        native_path = Path(geode_functions.data_file_path(point_set_id, data.native_file))
        upload_path = Path(geode_functions.upload_file_path("georeferenced.og_pts3d"))
    upload_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(native_path, upload_path)
    try:
        response = client.post(
            "/opengeodeweb_back/save_viewable_file",
            json={"geode_object_type": "PointSet3D", "filename": "georeferenced.og_pts3d"},
        )
    finally:
        upload_path.unlink()
    assert response.status_code == 200
    assert response.get_json()["crs"] == LAMBERT
    # The copy lives in the shared test data folder: it must not outlive the test
    assert not upload_path.exists()


def _attribute_count(client: FlaskClient, data_id: str) -> int:
    with client.application.app_context():
        geode_object = geode_functions.load_geode_object(data_id)
    assert isinstance(geode_object, GeodePointSet3D)
    return len(geode_object.point_set.vertex_attribute_manager().attribute_ids())


def test_round_trips_do_not_grow_the_native_file(client: FlaskClient) -> None:
    convert_route = "/opengeodeweb_back/crs/convert_geographic"
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    client.post("/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **LAMBERT})
    client.post(convert_route, json={"id": point_set_id, **UTM})
    client.post(convert_route, json={"id": point_set_id, **LAMBERT})
    attribute_count = _attribute_count(client, point_set_id)

    for _ in range(2):
        client.post(convert_route, json={"id": point_set_id, **UTM})
        client.post(convert_route, json={"id": point_set_id, **LAMBERT})
    assert _attribute_count(client, point_set_id) == attribute_count


def test_unknown_crs(client: FlaskClient) -> None:
    unknown = {"authority": "FOO", "code": "1", "name": "Unknown"}
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]

    response = client.post(
        "/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **unknown}
    )
    assert response.status_code == 400
    response = client.post(
        "/opengeodeweb_back/crs/align",
        json={
            "id": _create_point_set(client),
            "source_points": SOURCE,
            "target_points": TARGET,
            **unknown,
        },
    )
    assert response.status_code == 400

    # The name comes from the CRS list, not from the request
    response = client.post(
        "/opengeodeweb_back/crs/assign_geographic",
        json={"id": point_set_id, **LAMBERT, "name": "Wrong name"},
    )
    assert response.get_json()["crs"] == LAMBERT
    response = client.post(
        "/opengeodeweb_back/crs/convert_geographic", json={"id": point_set_id, **unknown}
    )
    assert response.status_code == 400


def test_assign_only_rewrites_the_native_file(client: FlaskClient) -> None:
    point_set_id = test_utils.check_save_viewable_file(
        client, "PointSet3D", "test.og_pts3d"
    ).get_json()["id"]
    with client.application.app_context():
        data = Data.get(point_set_id)
        assert data is not None
        assert data.viewable_file is not None
        viewable_path = Path(geode_functions.data_file_path(point_set_id, data.viewable_file))
    viewable_mtime = viewable_path.stat().st_mtime_ns

    response = client.post(
        "/opengeodeweb_back/crs/assign_geographic", json={"id": point_set_id, **LAMBERT}
    )
    assert response.status_code == 200
    assert viewable_path.stat().st_mtime_ns == viewable_mtime


def test_unreadable_crs_does_not_fail_the_data_response(monkeypatch: pytest.MonkeyPatch) -> None:
    def unreadable(*_args: object) -> None:
        msg = "unreadable CRS"
        raise RuntimeError(msg)

    monkeypatch.setattr(crs_functions, "geographic_info", unreadable)
    assert crs_functions.active_crs(GeodePointSet3D()) is None


def test_proj_finds_its_database() -> None:
    # Packaged apps move libproj away from the opengeode share folder
    assert (Path(os.environ["PROJ_DATA"]) / "proj.db").is_file()

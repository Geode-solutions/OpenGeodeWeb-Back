from __future__ import annotations

# Standard library imports
from typing import TYPE_CHECKING

# Third party imports
# Local application imports
from opengeodeweb_back import test_utils

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

from __future__ import annotations

# Standard library imports
import http.client
import logging
import os
import shutil
import urllib.request
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import opengeode_geosciences as og_geosciences
import pytest
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database.data import Data

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.basemap import basemap_mesh, basemap_providers, basemap_tiles
from opengeodeweb_back.routes.basemap import blueprint_basemap

if TYPE_CHECKING:
    from flask.testing import FlaskClient

TILES_FOLDER = Path(__file__).parent / "data" / "basemap_tiles"
HALF_WORLD = 20037508.342789244
BUILD_ROUTE = "/opengeodeweb_back/basemap/build"
DELETE_ROUTE = "/opengeodeweb_back/basemap/delete"
LAMBERT_JSON = {"authority": "EPSG", "code": "2154", "name": "RGF93 v1 / Lambert-93"}
PARIS_BOUNDS = {
    "x_min": 650_000.0,
    "y_min": 6_860_000.0,
    "x_max": 655_000.0,
    "y_max": 6_865_000.0,
}


@pytest.fixture
def local_tiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    monkeypatch.setenv("BASEMAP_TILE_URL_SATELLITE", TILES_FOLDER.as_uri() + "/{z}/{x}/{y}.png")
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    return tmp_path


@pytest.fixture
def any_tile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    # Same tile whatever z, x, y: routes get every tile at any zoom
    monkeypatch.setenv("BASEMAP_TILE_URL_SATELLITE", (TILES_FOLDER / "1" / "0" / "0.png").as_uri())
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    return tmp_path


def test_tile_range_whole_world() -> None:
    tiles = basemap_tiles.tile_range((-HALF_WORLD, -HALF_WORLD, HALF_WORLD, HALF_WORLD), 256, 512)
    assert tiles == basemap_tiles.TileRange(1, 0, 1, 0, 1)
    assert tiles.bounds_3857() == pytest.approx((-HALF_WORLD, -HALF_WORLD, HALF_WORLD, HALF_WORLD))


def test_tile_range_keeps_the_image_small() -> None:
    tiles = basemap_tiles.tile_range((0, 0, 10_000, 10_000), 256)
    width = (tiles.x_max - tiles.x_min + 1) * 256
    height = (tiles.y_max - tiles.y_min + 1) * 256
    assert max(width, height) <= 2048
    assert tiles.z <= 19


def test_tile_url_needs_a_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARCGIS_API_KEY", raising=False)
    monkeypatch.delenv("BASEMAP_TILE_URL_SATELLITE", raising=False)
    with pytest.raises(basemap_providers.MissingApiKeyError):
        basemap_providers.tile_url("satellite", 1, 0, 0)
    monkeypatch.setenv("ARCGIS_API_KEY", "key")
    assert basemap_providers.tile_url("satellite", 3, 1, 2).endswith("/tile/3/2/1?token=key")


@pytest.mark.usefixtures("local_tiles")
def test_fetch_and_save_tiles(tmp_path: Path) -> None:
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    images = basemap_tiles.fetch_tiles("satellite", tiles)
    assert all(images.values())
    folder = tmp_path / "tiles"
    basemap_tiles.save_tiles(tiles, images, folder)
    # Column then row, from the north-west corner
    assert sorted(path.name for path in folder.iterdir()) == [
        "0_0.png",
        "0_1.png",
        "1_0.png",
        "1_1.png",
    ]
    assert (folder / "1_1.png").read_bytes() == (TILES_FOLDER / "1" / "1" / "1.png").read_bytes()


@pytest.mark.usefixtures("local_tiles")
def test_missing_tile_is_not_written(tmp_path: Path) -> None:
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    images = basemap_tiles.fetch_tiles("satellite", tiles)
    images[(1, 1)] = None
    basemap_tiles.save_tiles(tiles, images, tmp_path)
    assert not (tmp_path / "1_1.png").exists()


def test_cached_tiles_are_not_fetched_again(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy = local_tiles / "copy"
    shutil.copytree(TILES_FOLDER, copy)
    monkeypatch.setenv("BASEMAP_TILE_URL_SATELLITE", copy.as_uri() + "/{z}/{x}/{y}.png")
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    basemap_tiles.fetch_tiles("satellite", tiles)
    shutil.rmtree(copy)
    assert all(basemap_tiles.fetch_tiles("satellite", tiles).values())


def test_invalid_cached_tile_is_fetched_again(local_tiles: Path) -> None:
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    basemap_tiles.fetch_tiles("satellite", tiles)
    cached_files = [path for path in local_tiles.rglob("*") if path.is_file()]
    assert len(cached_files) == 4
    for path in cached_files:
        path.write_bytes(b"\x89PN")
    images = basemap_tiles.fetch_tiles("satellite", tiles)
    assert images[(1, 1)] == (TILES_FOLDER / "1" / "1" / "1.png").read_bytes()
    assert all(path.read_bytes().startswith(b"\x89PNG") for path in cached_files)


@pytest.mark.usefixtures("local_tiles")
def test_failing_cache_write_still_returns_the_tile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(blocker))
    images = basemap_tiles.fetch_tiles("satellite", basemap_tiles.TileRange(1, 0, 1, 0, 1))
    assert all(images.values())


@pytest.mark.usefixtures("local_tiles")
def test_truncated_download_is_a_missing_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    def truncated(*_args: object, **_kwargs: object) -> None:
        partial = b""
        raise http.client.IncompleteRead(partial)

    monkeypatch.setattr(urllib.request, "urlopen", truncated)
    images = basemap_tiles.fetch_tiles("satellite", basemap_tiles.TileRange(1, 0, 1, 0, 1))
    assert not any(images.values())


def test_other_url_template_does_not_reuse_the_cache(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    basemap_tiles.fetch_tiles("satellite", tiles)
    missing = local_tiles / "missing"
    monkeypatch.setenv("BASEMAP_TILE_URL_SATELLITE", missing.as_uri() + "/{z}/{x}/{y}.png")
    assert not any(basemap_tiles.fetch_tiles("satellite", tiles).values())


def test_non_image_tile_is_neither_returned_nor_cached(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = local_tiles / "fake" / "1"
    for x in range(2):
        (fake / str(x)).mkdir(parents=True)
        for y in range(2):
            (fake / str(x) / f"{y}.png").write_text("<html>invalid token</html>")
    monkeypatch.setenv(
        "BASEMAP_TILE_URL_SATELLITE", (local_tiles / "fake").as_uri() + "/{z}/{x}/{y}.png"
    )
    cache = local_tiles / "cache"
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(cache))
    images = basemap_tiles.fetch_tiles("satellite", basemap_tiles.TileRange(1, 0, 1, 0, 1))
    assert not any(images.values())
    assert not any(path.is_file() for path in cache.rglob("*"))


LAMBERT = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "2154", "RGF93 v1 / Lambert-93")
# Around Paris in Lambert-93
PARIS = (650_000.0, 6_860_000.0, 655_000.0, 6_865_000.0)


def test_bounds_to_3857_paris() -> None:
    x_min, y_min, x_max, y_max = basemap_mesh.bounds_to_3857(PARIS, LAMBERT)
    # Paris is around 2.3 E, 48.8 N: x ~ 260 km, y ~ 6 250 km in Web Mercator
    assert 200_000 < x_min < x_max < 320_000
    assert 6_200_000 < y_min < y_max < 6_300_000


WEB_MERCATOR = og_geosciences.GeographicCoordinateSystemInfo(
    "EPSG", "3857", "WGS 84 / Pseudo-Mercator"
)


def test_bounds_already_in_web_mercator() -> None:
    bounds = (260_000.0, 6_250_000.0, 265_000.0, 6_255_000.0)
    assert basemap_mesh.bounds_to_3857(bounds, WEB_MERCATOR) == bounds
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        basemap_mesh.bounds_to_3857((0.0, 0.0, 1.0, 2 * HALF_WORLD), WEB_MERCATOR)


def test_bounds_outside_web_mercator() -> None:
    wgs84 = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "4326", "WGS 84")
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        # EPSG:4326 axis order is (latitude, longitude)
        basemap_mesh.bounds_to_3857((86.0, 0.0, 87.0, 1.0), wgs84)


def test_build_mesh() -> None:
    tiles = basemap_tiles.tile_range(basemap_mesh.bounds_to_3857(PARIS, LAMBERT), 256)
    mesh = basemap_mesh.build_mesh(tiles, LAMBERT, -12.5, "basemap")
    surface = mesh.triangulated_surface
    assert surface.nb_vertices() == basemap_mesh.GRID_SIZE**2
    assert surface.nb_polygons() == 2 * (basemap_mesh.GRID_SIZE - 1) ** 2
    manager = surface.main_coordinate_reference_system_manager()
    assert manager.active_coordinate_reference_system_name() == "EPSG:2154"
    attributes = surface.vertex_attribute_manager()
    (uv_id,) = attributes.attribute_ids_matching_name(basemap_mesh.UV_ATTRIBUTE)
    uv = attributes.find_attribute_variable_arraydouble2(uv_id)
    first, last = uv.value(0), uv.value(surface.nb_vertices() - 1)
    assert (first[0], first[1]) == pytest.approx((0.0, 0.0))
    assert (last[0], last[1]) == pytest.approx((1.0, 1.0))
    # The mesh covers the data, in Lambert-93, at the requested height
    point = surface.point(0)
    assert point.value(0) < PARIS[0]
    assert point.value(1) < PARIS[1]
    assert point.value(2) == pytest.approx(-12.5)


def test_build_mesh_in_web_mercator() -> None:
    tiles = basemap_tiles.TileRange(1, 0, 1, 0, 1)
    surface = basemap_mesh.build_mesh(tiles, WEB_MERCATOR, 0.0, "basemap").triangulated_surface
    manager = surface.main_coordinate_reference_system_manager()
    assert manager.active_coordinate_reference_system_name() == "EPSG:3857"
    assert surface.point(0).value(0) == pytest.approx(-HALF_WORLD)


def test_build_mesh_outside_the_project_crs() -> None:
    utm = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "32631", "WGS 84 / UTM zone 31N")
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        basemap_mesh.build_mesh(basemap_tiles.TileRange(0, 0, 0, 0, 0), utm, 0.0, "basemap")


@pytest.mark.usefixtures("any_tile")
def test_build_route(client: FlaskClient) -> None:
    response = client.post(
        BUILD_ROUTE,
        json={"style": "satellite", "bounds": PARIS_BOUNDS, "crs": LAMBERT_JSON, "z": 0.0},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert body["tiles_folder"] == "tiles"
    assert body["columns"] >= 1
    assert body["rows"] >= 1
    assert body["attribution"].startswith("Powered by Esri")
    assert body["crs"] == LAMBERT_JSON
    with client.application.app_context():
        tiles_path = Path(geode_functions.data_file_path(body["id"], "tiles"))
    assert tiles_path.is_dir()


def test_build_route_errors(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ARCGIS_API_KEY", raising=False)
    monkeypatch.delenv("BASEMAP_TILE_URL_SATELLITE", raising=False)
    params = {"style": "satellite", "bounds": PARIS_BOUNDS, "crs": LAMBERT_JSON, "z": 0.0}
    response = client.post(BUILD_ROUTE, json=params)
    assert response.status_code == 400
    assert "no API key" in response.get_json()["description"]

    unknown = {"authority": "FOO", "code": "1", "name": "x"}
    assert client.post(BUILD_ROUTE, json={**params, "crs": unknown}).status_code == 400

    # EPSG:4326 follows the authority axis order: x is the latitude
    wgs84 = {"authority": "EPSG", "code": "4326", "name": "WGS 84"}
    polar = {"x_min": 86.0, "y_min": 0.0, "x_max": 87.0, "y_max": 1.0}
    response = client.post(BUILD_ROUTE, json={**params, "crs": wgs84, "bounds": polar})
    assert response.status_code == 400


@pytest.mark.usefixtures("any_tile")
def test_build_route_web_mercator(client: FlaskClient) -> None:
    crs = {"authority": "EPSG", "code": "3857", "name": "WGS 84 / Pseudo-Mercator"}
    bounds = {"x_min": 260_000.0, "y_min": 6_250_000.0, "x_max": 265_000.0, "y_max": 6_255_000.0}
    response = client.post(
        BUILD_ROUTE, json={"style": "satellite", "bounds": bounds, "crs": crs, "z": 0.0}
    )
    assert response.status_code == 200
    assert response.get_json()["crs"] == crs


@pytest.mark.usefixtures("local_tiles")
def test_build_route_without_any_tile(
    client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    # The fixture only has zoom 1 tiles: none exists at the Paris zoom
    with get_session() as session:
        count = session.query(Data).count()
    with caplog.at_level(logging.WARNING):
        response = client.post(
            BUILD_ROUTE,
            json={"style": "satellite", "bounds": PARIS_BOUNDS, "crs": LAMBERT_JSON, "z": 0.0},
        )
    assert response.status_code == 502
    assert "no tile could be downloaded" in response.get_json()["description"]
    with get_session() as session:
        assert session.query(Data).count() == count
    assert "satellite" in caplog.text
    assert TILES_FOLDER.as_uri() not in caplog.text


@pytest.mark.usefixtures("any_tile")
def test_delete_route(client: FlaskClient) -> None:
    response = client.post(
        BUILD_ROUTE,
        json={"style": "satellite", "bounds": PARIS_BOUNDS, "crs": LAMBERT_JSON, "z": 0.0},
    )
    data_id = response.get_json()["id"]
    with client.application.app_context():
        folder = Path(geode_functions.data_file_path(data_id))
    assert folder.is_dir()
    response = client.post(DELETE_ROUTE, json={"id": data_id})
    assert response.status_code == 200
    assert not folder.exists()
    with get_session() as session:
        assert session.get(Data, data_id) is None
    assert client.post(DELETE_ROUTE, json={"id": data_id}).status_code == 404


@pytest.mark.usefixtures("any_tile")
def test_build_route_geographic_crs(client: FlaskClient) -> None:
    # EPSG:4326 follows the authority axis order: x is the latitude
    wgs84 = {"authority": "EPSG", "code": "4326", "name": "WGS 84"}
    bounds = {"x_min": 48.85, "y_min": 2.34, "x_max": 48.86, "y_max": 2.36}
    response = client.post(
        BUILD_ROUTE,
        json={"style": "satellite", "bounds": bounds, "crs": wgs84, "z": 0.0},
    )
    assert response.status_code == 200
    assert response.get_json()["tiles_folder"] == "tiles"


def test_padding_is_in_metres() -> None:
    padded = blueprint_basemap.padded((5.0, 7.0, 5.0, 7.0))
    assert padded[2] - padded[0] >= 1_000.0
    assert padded[3] - padded[1] >= 1_000.0
    assert (padded[0] + padded[2]) / 2 == pytest.approx(5.0)
    assert (padded[1] + padded[3]) / 2 == pytest.approx(7.0)
    wide = blueprint_basemap.padded((0.0, 0.0, 10_000.0, 4_000.0))
    assert wide == pytest.approx((-5_000.0, -2_000.0, 15_000.0, 6_000.0))


@pytest.mark.skipif("ARCGIS_API_KEY" not in os.environ, reason="needs a real Esri API key")
def test_esri_default_urls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    for style in basemap_providers.STYLES:
        monkeypatch.delenv(f"BASEMAP_TILE_URL_{style.upper()}", raising=False)
        images = basemap_tiles.fetch_tiles(style, basemap_tiles.TileRange(1, 0, 0, 0, 0))
        assert images[(0, 0)], f"{style} default URL returned no tile"

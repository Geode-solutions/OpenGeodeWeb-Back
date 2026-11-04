from __future__ import annotations

# Standard library imports
import http.client
import io
import logging
import shutil
import ssl
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from email.message import Message
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import opengeode_geosciences as og_geosciences
import pytest
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database.data import Data
from PIL import Image

# Local application imports
from opengeodeweb_back import geode_functions
from opengeodeweb_back.basemap import basemap_mesh, basemap_providers, basemap_tiles
from opengeodeweb_back.routes.basemap import blueprint_basemap

if TYPE_CHECKING:
    from flask.testing import FlaskClient
    from werkzeug.test import TestResponse

TILES_FOLDER = Path(__file__).parent / "data" / "basemap_tiles"
ANY_TILE = TILES_FOLDER / "1" / "0" / "0.png"
HALF_WORLD = basemap_tiles.HALF_WORLD
BUILD_ROUTE = "/opengeodeweb_back/basemap/build"
DELETE_ROUTE = "/opengeodeweb_back/basemap/delete"
LAMBERT = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "2154", "RGF93 v1 / Lambert-93")
LAMBERT_JSON = {"authority": "EPSG", "code": "2154", "name": "RGF93 v1 / Lambert-93"}
# Around Paris in Lambert-93
PARIS = (650_000.0, 6_860_000.0, 655_000.0, 6_865_000.0)
PARIS_BOUNDS = dict(zip(("x_min", "y_min", "x_max", "y_max"), PARIS, strict=True))
WGS84_JSON = {"authority": "EPSG", "code": "4326", "name": "WGS 84"}
WHOLE_WORLD = basemap_tiles.TileRange(1, 0, 1, 0, 1)


def _serve(monkeypatch: pytest.MonkeyPatch, cache: Path, template: str) -> None:
    for source in basemap_providers.SOURCES:
        monkeypatch.setenv(f"BASEMAP_TILE_URL_{source.upper()}", template)
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(cache))


@pytest.fixture
def local_tiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Path:
    _serve(monkeypatch, tmp_path, TILES_FOLDER.as_uri() + "/{z}/{x}/{y}.png")
    return tmp_path


@pytest.fixture
def any_tile(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Same tile whatever z, x, y: routes get every tile at any zoom
    _serve(monkeypatch, tmp_path, ANY_TILE.as_uri())


def _build(client: FlaskClient, **params: object) -> TestResponse:
    json = {"maps": ["satellite"], "bounds": PARIS_BOUNDS, "crs": LAMBERT_JSON, "z": 0.0}
    return client.post(BUILD_ROUTE, json={**json, **params})


def test_tile_range_whole_world() -> None:
    tiles = basemap_tiles.tile_range((-HALF_WORLD, -HALF_WORLD, HALF_WORLD, HALF_WORLD), 19, 512)
    assert tiles == basemap_tiles.TileRange(1, 0, 1, 0, 1)
    assert tiles.bounds_3857() == pytest.approx((-HALF_WORLD, -HALF_WORLD, HALF_WORLD, HALF_WORLD))


def test_tile_range_keeps_the_image_small() -> None:
    tiles = basemap_tiles.tile_range((0, 0, 10_000, 10_000), 19)
    width = (tiles.x_max - tiles.x_min + 1) * 256
    height = (tiles.y_max - tiles.y_min + 1) * 256
    assert max(width, height) <= 2048
    assert tiles.z <= 19


@pytest.mark.usefixtures("local_tiles")
def test_fetch_and_save_tiles(tmp_path: Path) -> None:
    images = basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    assert all(images.values())
    expected = images[(1, 1)]
    # A missing tile is not written
    images[(1, 0)] = None
    folder = tmp_path / "tiles"
    basemap_tiles.save_tiles(WHOLE_WORLD, images, folder)
    # Column then row, from the north-west corner
    assert sorted(path.name for path in folder.iterdir()) == ["0_0.png", "0_1.png", "1_1.png"]
    assert expected == (TILES_FOLDER / "1" / "1" / "1.png").read_bytes()
    assert (folder / "1_1.png").read_bytes() == expected


@pytest.mark.usefixtures("local_tiles")
def test_fetch_sources_downloads_every_source() -> None:
    images = basemap_tiles.fetch_sources(["ign_orthophotos", "ign_roads"], WHOLE_WORLD)
    assert list(images) == ["ign_orthophotos", "ign_roads"]
    assert all(all(source.values()) for source in images.values())


def test_cached_tiles_are_not_fetched_again(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    copy = local_tiles / "copy"
    shutil.copytree(TILES_FOLDER, copy)
    monkeypatch.setenv("BASEMAP_TILE_URL_IGN_ORTHOPHOTOS", copy.as_uri() + "/{z}/{x}/{y}.png")
    basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    shutil.rmtree(copy)
    assert all(basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD).values())


def test_invalid_cached_tile_is_fetched_again(local_tiles: Path) -> None:
    basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    cached_files = [path for path in local_tiles.rglob("*") if path.is_file()]
    assert len(cached_files) == 4
    for path in cached_files:
        path.write_bytes(b"\x89PN")
    images = basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    assert images[(1, 1)] == (TILES_FOLDER / "1" / "1" / "1.png").read_bytes()
    assert all(path.read_bytes().startswith(b"\x89PNG") for path in cached_files)


@pytest.mark.usefixtures("local_tiles")
def test_failing_cache_write_still_returns_the_tile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    blocker = tmp_path / "blocker"
    blocker.write_text("not a folder")
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(blocker))
    images = basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    assert all(images.values())


@pytest.mark.usefixtures("local_tiles")
def test_truncated_download_is_a_missing_tile(monkeypatch: pytest.MonkeyPatch) -> None:
    def truncated(*_args: object, **_kwargs: object) -> None:
        partial = b""
        raise http.client.IncompleteRead(partial)

    monkeypatch.setattr(urllib.request, "urlopen", truncated)
    images = basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    assert not any(images.values())


@pytest.mark.usefixtures("local_tiles")
def test_tile_not_found_is_not_requested_again(monkeypatch: pytest.MonkeyPatch) -> None:
    requests: list[str] = []

    def not_found(request: urllib.request.Request, timeout: float, context: object) -> None:  # noqa: ARG001
        requests.append(request.full_url)
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", Message(), None)

    monkeypatch.setattr(urllib.request, "urlopen", not_found)
    tiles = basemap_tiles.TileRange(1, 0, 0, 0, 0)
    assert basemap_tiles.fetch_tiles("ign_orthophotos", tiles) == {(0, 0): None}
    assert basemap_tiles.fetch_tiles("ign_orthophotos", tiles) == {(0, 0): None}
    assert len(requests) == 1


def test_other_url_template_does_not_reuse_the_cache(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    missing = local_tiles / "missing"
    monkeypatch.setenv("BASEMAP_TILE_URL_IGN_ORTHOPHOTOS", missing.as_uri() + "/{z}/{x}/{y}.png")
    assert not any(basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD).values())


def test_non_image_tile_is_neither_returned_nor_cached(
    local_tiles: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = local_tiles / "fake" / "1"
    for x in range(2):
        (fake / str(x)).mkdir(parents=True)
        for y in range(2):
            (fake / str(x) / f"{y}.png").write_text("<html>invalid token</html>")
    monkeypatch.setenv(
        "BASEMAP_TILE_URL_IGN_ORTHOPHOTOS", (local_tiles / "fake").as_uri() + "/{z}/{x}/{y}.png"
    )
    cache = local_tiles / "cache"
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(cache))
    images = basemap_tiles.fetch_tiles("ign_orthophotos", WHOLE_WORLD)
    assert not any(images.values())
    assert not any(path.is_file() for path in cache.rglob("*"))


def test_bounds_to_3857_paris() -> None:
    x_min, y_min, x_max, y_max = basemap_mesh.bounds_to_3857(PARIS, LAMBERT)
    # Paris is around 2.3 E, 48.8 N: x ~ 260 km, y ~ 6 250 km in Web Mercator
    assert 200_000 < x_min < x_max < 320_000
    assert 6_200_000 < y_min < y_max < 6_300_000


def test_bounds_already_in_web_mercator() -> None:
    bounds = (260_000.0, 6_250_000.0, 265_000.0, 6_255_000.0)
    assert basemap_mesh.bounds_to_3857(bounds, basemap_mesh.WEB_MERCATOR) == bounds
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        basemap_mesh.bounds_to_3857((0.0, 0.0, 1.0, 2 * HALF_WORLD), basemap_mesh.WEB_MERCATOR)


def test_bounds_outside_web_mercator() -> None:
    wgs84 = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "4326", "WGS 84")
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        # EPSG:4326 axis order is (latitude, longitude)
        basemap_mesh.bounds_to_3857((86.0, 0.0, 87.0, 1.0), wgs84)


def test_build_mesh() -> None:
    tiles = basemap_tiles.tile_range(basemap_mesh.bounds_to_3857(PARIS, LAMBERT), 19)
    mesh = basemap_mesh.build_mesh(tiles, LAMBERT, -12.5)
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
    mesh = basemap_mesh.build_mesh(WHOLE_WORLD, basemap_mesh.WEB_MERCATOR, 0.0)
    surface = mesh.triangulated_surface
    manager = surface.main_coordinate_reference_system_manager()
    assert manager.active_coordinate_reference_system_name() == "EPSG:3857"
    assert surface.point(0).value(0) == pytest.approx(-HALF_WORLD)


def test_build_mesh_outside_the_project_crs() -> None:
    utm = og_geosciences.GeographicCoordinateSystemInfo("EPSG", "32631", "WGS 84 / UTM zone 31N")
    with pytest.raises(basemap_mesh.OutsideProjectionError):
        basemap_mesh.build_mesh(basemap_tiles.TileRange(0, 0, 0, 0, 0), utm, 0.0)


@pytest.mark.usefixtures("any_tile")
def test_build_route(client: FlaskClient) -> None:
    response = _build(client, maps=["routes", "satellite"])
    assert response.status_code == 200
    body = response.get_json()
    assert body["maps"] == [
        {"map": "satellite", "sources": ["eox_s2cloudless_2016", "ign_orthophotos"]},
        {"map": "routes", "sources": ["ign_roads"]},
    ]
    assert body["attribution"].startswith("Sentinel-2 cloudless 2016 by EOX")
    assert body["attribution"].endswith("© IGN")
    assert body["columns"] >= 1
    assert body["rows"] >= 1
    assert body["crs"] == LAMBERT_JSON
    with client.application.app_context():
        tiles_path = Path(geode_functions.data_file_path(body["id"], "tiles"))
    assert sorted(path.name for path in tiles_path.iterdir()) == [
        "eox_s2cloudless_2016",
        "ign_orthophotos",
        "ign_roads",
    ]


def test_build_route_errors(client: FlaskClient) -> None:
    unknown = {"authority": "FOO", "code": "1", "name": "x"}
    assert _build(client, crs=unknown).status_code == 400
    assert _build(client, maps=[]).status_code == 400
    assert _build(client, maps=["topo"]).status_code == 400
    assert _build(client, max_pixels=100).status_code == 400
    assert _build(client, max_pixels=5000).status_code == 400
    # EPSG:4326 follows the authority axis order: x is the latitude
    polar = {"x_min": 86.0, "y_min": 0.0, "x_max": 87.0, "y_max": 1.0}
    assert _build(client, crs=WGS84_JSON, bounds=polar).status_code == 400


@pytest.mark.usefixtures("local_tiles")
def test_build_route_without_any_tile(
    client: FlaskClient, caplog: pytest.LogCaptureFixture
) -> None:
    # The fixture only has zoom 1 tiles: none exists at the Paris zoom
    with get_session() as session:
        count = session.query(Data).count()
    with caplog.at_level(logging.WARNING):
        response = _build(client)
    assert response.status_code == 502
    assert "no tile could be downloaded" in response.get_json()["description"]
    with get_session() as session:
        assert session.query(Data).count() == count
    assert "satellite" in caplog.text
    assert "zoom" in caplog.text
    assert TILES_FOLDER.as_uri() not in caplog.text


@pytest.mark.usefixtures("any_tile")
def test_delete_route(client: FlaskClient) -> None:
    data_id = _build(client).get_json()["id"]
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
    bounds = {"x_min": 48.85, "y_min": 2.34, "x_max": 48.86, "y_max": 2.36}
    assert _build(client, crs=WGS84_JSON, bounds=bounds).status_code == 200


@pytest.mark.usefixtures("any_tile")
def test_build_route_detail_without_margin(client: FlaskClient) -> None:
    # Same pixel budget on both sides, so only the margin differs
    base = _build(client, max_pixels=512).get_json()
    detail = _build(client, margin=False, max_pixels=512).get_json()
    # Without margin the mesh stays close to the requested bounds, at a finer zoom
    assert detail["zoom"] >= base["zoom"]
    assert detail["columns"] * 256 <= 512
    width = detail["bounds"]["x_max"] - detail["bounds"]["x_min"]
    base_width = base["bounds"]["x_max"] - base["bounds"]["x_min"]
    assert width < base_width
    assert base["bounds"]["x_min"] <= PARIS_BOUNDS["x_min"]


def test_build_route_skips_sources_without_tiles(
    client: FlaskClient, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Outside France: no IGN tile, the world imagery alone makes the map
    _serve(monkeypatch, tmp_path / "cache", (tmp_path / "none").as_uri() + "/{z}/{x}/{y}.png")
    monkeypatch.setenv("BASEMAP_TILE_URL_EOX_S2CLOUDLESS_2016", ANY_TILE.as_uri())
    monkeypatch.setenv("BASEMAP_TILE_URL_EOX_OVERLAY", ANY_TILE.as_uri())
    response = _build(client, maps=["satellite", "routes"])
    assert response.status_code == 200
    body = response.get_json()
    assert body["maps"][1] == {"map": "routes", "sources": ["eox_overlay"]}
    assert "IGN" not in body["attribution"]
    assert "rendering © EOX" in body["attribution"]
    with client.application.app_context():
        tiles_path = Path(geode_functions.data_file_path(body["id"], "tiles"))
    # Only the drawn sources have a tiles folder
    assert not (tiles_path / "ign_roads").exists()


def test_padding_is_in_metres() -> None:
    padded = blueprint_basemap.padded((5.0, 7.0, 5.0, 7.0))
    assert padded[2] - padded[0] >= 1_000.0
    assert padded[3] - padded[1] >= 1_000.0
    assert (padded[0] + padded[2]) / 2 == pytest.approx(5.0)
    assert (padded[1] + padded[3]) / 2 == pytest.approx(7.0)
    wide = blueprint_basemap.padded((0.0, 0.0, 10_000.0, 4_000.0))
    assert wide == pytest.approx((-5_000.0, -2_000.0, 15_000.0, 6_000.0))


def test_url_template_from_the_source_table(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("BASEMAP_TILE_URL_IGN_ROADS", raising=False)
    url = basemap_providers.url_template("ign_roads").format(z=14, x=8298, y=5636)
    assert url.startswith("https://data.geopf.fr/wmts?")
    assert "LAYER=TRANSPORTNETWORKS.ROADS" in url
    assert "TILEMATRIX=14&TILEROW=5636&TILECOL=8298" in url
    monkeypatch.setenv("BASEMAP_TILE_URL_IGN_ROADS", "http://local/{z}/{x}/{y}.png")
    assert basemap_providers.url_template("ign_roads") == "http://local/{z}/{x}/{y}.png"


def test_maps_from_the_bottom_up() -> None:
    # Whatever the requested order: satellite, plan, then routes
    assert basemap_providers.sorted_maps(["routes", "satellite"]) == ["satellite", "routes"]
    assert basemap_providers.max_zoom(["eox_s2cloudless_2016", "ign_roads"]) == 18
    assert basemap_providers.max_zoom(["eox_overlay", "ign_orthophotos"]) == 19


def test_map_layers_stack_or_take_the_first_served() -> None:
    served = {"eox_s2cloudless_2016", "ign_orthophotos", "eox_overlay"}
    layers = basemap_providers.map_layers(["satellite", "routes"], lambda source: source in served)
    # Satellite stacks its sources; routes take the IGN when served, else EOX
    assert layers == {
        "satellite": ["eox_s2cloudless_2016", "ign_orthophotos"],
        "routes": ["eox_overlay"],
    }
    layers = basemap_providers.map_layers(["routes"], lambda _source: True)
    assert layers == {"routes": ["ign_roads"]}
    # A map without any served source is left out
    assert basemap_providers.map_layers(["routes"], lambda _source: False) == {}


def test_attribution_once_per_provider() -> None:
    assert (
        basemap_providers.attribution(["ign_orthophotos", "ign_roads", "osm"])
        == "© IGN | © OpenStreetMap contributors"
    )


def test_tile_range_stops_at_the_max_zoom() -> None:
    # A tiny extent would go up to zoom 19: the sources stop earlier
    tiny = (261_000.0, 6_251_000.0, 261_010.0, 6_251_010.0)
    assert basemap_tiles.tile_range(tiny, 12).z == 12


@pytest.mark.usefixtures("local_tiles")
def test_tiles_past_the_max_zoom_are_cut_from_their_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = basemap_providers.SOURCES["ign_roads"]
    monkeypatch.setitem(
        basemap_providers.SOURCES,
        "ign_roads",
        basemap_providers.Source(source.url_template, 1, source.attribution),
    )
    images = basemap_tiles.fetch_tiles("ign_roads", basemap_tiles.TileRange(2, 0, 1, 0, 1))
    assert len(images) == 4
    with Image.open(TILES_FOLDER / "1" / "0" / "0.png") as parent:
        for (x, y), content in images.items():
            assert content is not None
            with Image.open(io.BytesIO(content)) as tile:
                assert tile.size == (256, 256)
                quadrant = parent.crop((x * 128, y * 128, x * 128 + 128, y * 128 + 128))
                expected = quadrant.resize((256, 256), Image.Resampling.BILINEAR)
                assert tile.tobytes() == expected.tobytes()


def test_tiles_are_requested_with_the_user_agent_and_certificates(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sent: list[tuple[str | None, object]] = []

    def capture(request: urllib.request.Request, timeout: float, context: object) -> None:  # noqa: ARG001
        sent.append((request.get_header("User-agent"), context))
        raise OSError

    monkeypatch.setattr(urllib.request, "urlopen", capture)
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", "/nonexistent")
    assert basemap_tiles.fetch_tiles("osm", basemap_tiles.TileRange(1, 0, 0, 0, 0)) == {
        (0, 0): None
    }
    assert sent == [(basemap_providers.USER_AGENT, basemap_tiles.SSL_CONTEXT)]
    # Packaged binaries verify the servers with the bundled certificates
    assert basemap_tiles.SSL_CONTEXT.verify_mode == ssl.CERT_REQUIRED


def test_requests_to_one_host_are_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    lock = threading.Lock()
    running: dict[str, int] = {}
    peak: dict[str, int] = {}

    def slow(request: urllib.request.Request, timeout: float, context: object) -> None:  # noqa: ARG001
        host = urllib.parse.urlparse(request.full_url).netloc
        with lock:
            running[host] = running.get(host, 0) + 1
            peak[host] = max(peak.get(host, 0), running[host])
        time.sleep(0.02)
        with lock:
            running[host] -= 1
        raise OSError

    monkeypatch.setattr(urllib.request, "urlopen", slow)
    _serve(monkeypatch, Path("/nonexistent"), "https://tiles.example/{z}/{x}/{y}.png")
    sources = ["ign_orthophotos", "ign_roads", "osm"]
    basemap_tiles.fetch_sources(sources, basemap_tiles.TileRange(4, 0, 3, 0, 3))
    assert peak["tiles.example"] == basemap_tiles.MAX_REQUESTS_PER_HOST


def test_corrupt_parent_tile_is_a_missing_tile() -> None:
    assert basemap_tiles._overzoomed(b"\x89PNG" + b"garbage" * 10, 1, 0, 0) is None  # noqa: SLF001


def test_palette_parent_tile_is_enlarged_smoothly() -> None:
    palette = Image.new("P", (256, 256))
    palette.putpalette([0, 0, 0, 255, 255, 255])
    palette.paste(1, (0, 0, 64, 256))
    buffer = io.BytesIO()
    palette.save(buffer, format="PNG")
    content = basemap_tiles._overzoomed(buffer.getvalue(), 1, 0, 0)  # noqa: SLF001
    assert content is not None
    with Image.open(io.BytesIO(content)) as tile:
        assert tile.mode in ("RGB", "RGBA")

from __future__ import annotations

# Standard library imports
import dataclasses
import io
import json
import math
import urllib.error
import urllib.request
from email.message import Message
from typing import TYPE_CHECKING, Self

# Third party imports
import pytest
from PIL import Image

# Local application imports
from opengeodeweb_back.basemap import basemap_providers, basemap_tiles, geology_registry

if TYPE_CHECKING:
    from pathlib import Path

ENTRY = {
    "id": "geology_test",
    "name": "Test 1/50 000",
    "provider": "Test",
    "area": [-5.0, 41.0, 10.0, 51.0],
    "level": "N3",
    "source_scale": 50000,
    "min_scale": 0,
    "max_scale": 80000,
    "protocol": "xyz",
    "url": "https://tiles.test/{z}/{x}/{y}.png",
    "layers": None,
    "styles": None,
    "format": "image/png",
    "supported_crs": ["EPSG:3857"],
    "max_zoom": 15,
    "empty_tile": "transparent",
    "licence": "CC BY 4.0",
    "attribution": "© Test",
    "status": "verified",
}


def _registry(tmp_path: Path, *entries: dict[str, object]) -> Path:
    path = tmp_path / "sources.json"
    path.write_text(json.dumps(list(entries)))
    return path


def test_registry_loads_verified_sources_most_detailed_first(tmp_path: Path) -> None:
    coarse = {**ENTRY, "id": "geology_coarse", "source_scale": 1_000_000, "area": None}
    unchecked = {**ENTRY, "id": "geology_unchecked", "status": "to_check"}
    sources = geology_registry.load(_registry(tmp_path, coarse, ENTRY, unchecked))
    # The most detailed first; unverified sources are never used
    assert list(sources) == ["geology_test", "geology_coarse"]
    test = sources["geology_test"]
    assert (test.min_scale, test.max_scale, test.source_scale) == (0, 80_000, 50_000)
    assert test.empty_tile == "transparent"
    assert sources["geology_coarse"].area_3857 is None
    # The area is kept in Web Mercator, like the tile grid
    assert test.area_3857 is not None
    assert test.area_3857[0] == pytest.approx(-556_597.45, abs=1)


@pytest.mark.parametrize(
    "change",
    [
        {"id": "brgm"},
        {"protocol": "wfs"},
        {"empty_tile": "white"},
        {"min_scale": 90_000},
        {"url": None},
        {"source_scale": None},
    ],
)
def test_invalid_registry_entry_names_the_entry(tmp_path: Path, change: dict[str, object]) -> None:
    with pytest.raises(geology_registry.RegistryError, match=r"geology_test|brgm"):
        geology_registry.load(_registry(tmp_path, {**ENTRY, **change}))


def test_duplicate_registry_ids_are_rejected(tmp_path: Path) -> None:
    with pytest.raises(geology_registry.RegistryError, match="geology_test"):
        geology_registry.load(_registry(tmp_path, ENTRY, ENTRY))


def test_shipped_registry_feeds_the_source_table() -> None:
    scales = [
        basemap_providers.SOURCES[source].source_scale or 0
        for source in basemap_providers.GEOLOGY_SOURCES
    ]
    assert scales == sorted(scales)
    for source in basemap_providers.GEOLOGY_SOURCES:
        assert source.startswith("geology_")
        assert source in basemap_providers.SOURCES
    # The sources of the other maps keep the defaults: one source for the whole mosaic
    assert basemap_providers.SOURCES["osm"].max_scale == math.inf


WMS_ENTRY = {
    **ENTRY,
    "id": "geology_wms",
    "protocol": "wms",
    "url": "https://wms.test/geology",
    "layers": "GEOLOGY",
    "styles": "",
    "format": "image/png",
}


def test_wms_source_asks_web_mercator_when_served(tmp_path: Path) -> None:
    wms = geology_registry.load(_registry(tmp_path, WMS_ENTRY))["geology_wms"]
    assert wms.wms_crs == "EPSG:3857"
    assert wms.url_template.startswith("https://wms.test/geology?SERVICE=WMS&VERSION=1.3.0")
    assert "REQUEST=GetMap&LAYERS=GEOLOGY&STYLES=&CRS=EPSG:3857&BBOX={bbox}" in wms.url_template
    assert "WIDTH=256&HEIGHT=256&FORMAT=image/png&TRANSPARENT=TRUE" in wms.url_template


def test_wms_source_without_web_mercator_asks_crs84(tmp_path: Path) -> None:
    entry = {**WMS_ENTRY, "supported_crs": ["EPSG:4326", "CRS:84"]}
    assert geology_registry.load(_registry(tmp_path, entry))["geology_wms"].wms_crs == "CRS:84"
    entry = {**WMS_ENTRY, "supported_crs": ["EPSG:2154"]}
    with pytest.raises(geology_registry.RegistryError, match="geology_wms"):
        geology_registry.load(_registry(tmp_path, entry))


def test_tile_bbox_in_the_wms_crs(monkeypatch: pytest.MonkeyPatch) -> None:
    half = basemap_tiles.HALF_WORLD
    mercator = basemap_providers.Source("u", 15, "a", wms_crs="EPSG:3857")
    degrees = basemap_providers.Source("u", 15, "a", wms_crs="CRS:84")
    latitude_first = basemap_providers.Source("u", 15, "a", wms_crs="EPSG:4326")
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_m", mercator)
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_d", degrees)
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_l", latitude_first)
    # Tile 1/1/0: the north-east quarter of the world
    assert basemap_tiles.tile_bbox("geology_m", 1, 1, 0) == f"0.0,0.0,{half},{half}"
    lon_min, lat_min, lon_max, lat_max = map(
        float, basemap_tiles.tile_bbox("geology_d", 1, 1, 0).split(",")
    )
    assert (lon_min, lat_min, lon_max) == pytest.approx((0, 0, 180))
    assert lat_max == pytest.approx(85.0511, abs=1e-3)
    # WMS 1.3.0 reads EPSG:4326 latitude first
    lat_min, lon_min, lat_max, lon_max = map(
        float, basemap_tiles.tile_bbox("geology_l", 1, 1, 0).split(",")
    )
    assert (lat_min, lon_min, lon_max) == pytest.approx((0, 0, 180))


def test_export_source_keeps_its_template(tmp_path: Path) -> None:
    template = "https://maps.test/server/rest/services/Geology/MapServer/export?bbox={bbox}&bboxSR=3857&size=256,256&f=image"
    entry = {**ENTRY, "id": "geology_export", "protocol": "export", "url": template}
    source = geology_registry.load(_registry(tmp_path, entry))["geology_export"]
    assert (source.url_template, source.wms_crs) == (template, "EPSG:3857")
    without_bbox = {**entry, "url": "https://maps.test/MapServer/export?f=image"}
    with pytest.raises(geology_registry.RegistryError, match="geology_export"):
        geology_registry.load(_registry(tmp_path, without_bbox))


WHOLE_WORLD = basemap_tiles.TileRange(1, 0, 1, 0, 1)


def _image(mode: str, colour: tuple[int, ...], image_format: str) -> bytes:
    output = io.BytesIO()
    Image.new(mode, (256, 256), colour).save(output, format=image_format)
    return output.getvalue()


def test_empty_tiles() -> None:
    white = _image("RGB", (255, 255, 255), "JPEG")
    clear = _image("RGBA", (0, 0, 0, 0), "PNG")
    coloured = _image("RGB", (200, 120, 40), "PNG")
    # The Géoplateforme answers a plain white JPEG outside its maps
    assert basemap_tiles.is_empty(white, "#ffffff")
    assert not basemap_tiles.is_empty(coloured, "#ffffff")
    assert basemap_tiles.is_empty(clear, "transparent")
    assert not basemap_tiles.is_empty(coloured, "transparent")
    # A 404 source never reads its tiles
    assert not basemap_tiles.is_empty(white, "404")


class _Answer:
    def __init__(self, content: bytes) -> None:
        self.content = content

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_args: object) -> None:
        pass

    def read(self) -> bytes:
        return self.content


def _source(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, **fields: object) -> None:
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    monkeypatch.delenv("BASEMAP_TILE_URL", raising=False)
    source = basemap_providers.Source("https://tiles.test/{z}/{x}/{y}.png", 15, "a", **fields)
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_t", source)


def test_empty_tile_is_missing_and_not_asked_again(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _source(monkeypatch, tmp_path, empty_tile="#ffffff")
    white = _image("RGB", (255, 255, 255), "JPEG")
    calls: list[str] = []

    def answer(request: urllib.request.Request, **_kwargs: object) -> _Answer:
        calls.append(request.full_url)
        return _Answer(white)

    monkeypatch.setattr(urllib.request, "urlopen", answer)
    assert not any(basemap_tiles.fetch_tiles("geology_t", WHOLE_WORLD).values())
    basemap_tiles.fetch_tiles("geology_t", WHOLE_WORLD)
    assert len(calls) == 4


def _too_many_requests(url: str) -> urllib.error.HTTPError:
    headers = Message()
    headers["Retry-After"] = "0"
    return urllib.error.HTTPError(url, 429, "Too Many Requests", headers, io.BytesIO())


def test_too_many_requests_waits_then_retries(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _source(monkeypatch, tmp_path)
    tile = _image("RGB", (200, 120, 40), "PNG")
    refused: set[str] = set()

    def once_refused(request: urllib.request.Request, **_kwargs: object) -> _Answer:
        if request.full_url not in refused:
            refused.add(request.full_url)
            raise _too_many_requests(request.full_url)
        return _Answer(tile)

    monkeypatch.setattr(urllib.request, "urlopen", once_refused)
    assert all(basemap_tiles.fetch_tiles("geology_t", WHOLE_WORLD).values())


def test_persistent_too_many_requests_is_a_missing_tile(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _source(monkeypatch, tmp_path)

    def always_refused(request: urllib.request.Request, **_kwargs: object) -> _Answer:
        raise _too_many_requests(request.full_url)

    monkeypatch.setattr(urllib.request, "urlopen", always_refused)
    assert not any(basemap_tiles.fetch_tiles("geology_t", WHOLE_WORLD).values())
    # Not cached: the server may answer later
    assert not any(path.is_file() for path in tmp_path.rglob("*"))
    assert "geology_t" in caplog.text


HALF = basemap_tiles.HALF_WORLD


def test_tile_scale_follows_zoom_and_latitude() -> None:
    # At the equator, zoom 9 is about 1/1 000 000
    assert basemap_tiles.tile_scale(9, 255) == pytest.approx(1_091_958, rel=0.01)
    # One zoom more halves the scale
    assert basemap_tiles.tile_scale(10, 511) == pytest.approx(545_979, rel=0.01)
    # At 60° north the ground is twice as small on the screen
    assert basemap_tiles.tile_scale(9, 148) == pytest.approx(1_091_958 / 2, rel=0.02)


def _two_sources(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    monkeypatch.delenv("BASEMAP_TILE_URL", raising=False)
    # A detailed national source on the west half of the world, then a coarse continental one
    national = basemap_providers.Source(
        "https://national.test/{z}/{x}/{y}.png",
        15,
        "© National",
        min_scale=0,
        max_scale=1e12,
        source_scale=50_000,
        area_3857=(-HALF, -HALF, 0.0, HALF),
        empty_tile="transparent",
    )
    continental = basemap_providers.Source(
        "https://continental.test/{z}/{x}/{y}.png",
        15,
        "© Continental",
        min_scale=0,
        max_scale=1e12,
        source_scale=1_000_000,
        empty_tile="transparent",
    )
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_national", national)
    monkeypatch.setitem(basemap_providers.SOURCES, "geology_continental", continental)
    tile = _image("RGB", (200, 120, 40), "PNG")
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_a, **_k: _Answer(tile))


def test_each_tile_takes_the_first_source_serving_it(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _two_sources(monkeypatch, tmp_path)
    images = basemap_tiles.fetch_layers([("geology_national", "geology_continental")], WHOLE_WORLD)
    # The west column from the national source, the east one from the continental source
    assert sorted(images["geology_national"]) == [(0, 0), (0, 1)]
    assert sorted(images["geology_continental"]) == [(1, 0), (1, 1)]


def test_a_failing_source_leaves_its_tiles_to_the_next(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _two_sources(monkeypatch, tmp_path)
    tile = _image("RGB", (200, 120, 40), "PNG")

    def national_down(request: urllib.request.Request, **_kwargs: object) -> _Answer:
        if "national" in request.full_url:
            raise TimeoutError
        return _Answer(tile)

    monkeypatch.setattr(urllib.request, "urlopen", national_down)
    images = basemap_tiles.fetch_layers([("geology_national", "geology_continental")], WHOLE_WORLD)
    assert list(images) == ["geology_continental"]
    assert len(images["geology_continental"]) == 4


def test_out_of_scale_source_is_not_asked(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _two_sources(monkeypatch, tmp_path)
    detailed = basemap_providers.SOURCES["geology_national"]
    monkeypatch.setitem(
        basemap_providers.SOURCES,
        "geology_national",
        dataclasses.replace(detailed, max_scale=80_000),
    )
    # A whole world view is far coarser than 1/80 000: the continental source alone fills it
    images = basemap_tiles.fetch_layers([("geology_national", "geology_continental")], WHOLE_WORLD)
    assert list(images) == ["geology_continental"]


def test_tiles_without_a_source_stay_empty(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _two_sources(monkeypatch, tmp_path)
    # No world fallback: the east column is left out, and the Viewer shows it transparent
    images = basemap_tiles.fetch_layers([("geology_national",)], WHOLE_WORLD)
    assert sorted(images["geology_national"]) == [(0, 0), (0, 1)]


def test_layers_without_scale_windows_keep_one_source_per_mosaic(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _two_sources(monkeypatch, tmp_path)
    monkeypatch.setitem(
        basemap_providers.SOURCES,
        "first",
        basemap_providers.Source("https://a.test/{z}/{x}/{y}.png", 15, "a"),
    )
    monkeypatch.setitem(
        basemap_providers.SOURCES,
        "second",
        basemap_providers.Source("https://b.test/{z}/{x}/{y}.png", 15, "b"),
    )
    assert list(basemap_tiles.fetch_layers([("first", "second")], WHOLE_WORLD)) == ["first"]


# A tile with data of every shipped geology source, z/x/y in Web Mercator
KNOWN_TILES = {
    "geology_brgm_50k": (13, 4164, 2922),
    "geology_brgm_250k": (10, 518, 352),
    "geology_brgm_1m": (8, 129, 88),
    "geology_usgs_sgmc": (12, 850, 1554),
    "geology_usgs_alaska": (10, 91, 267),
    "geology_usgs_hawaii": (10, 70, 455),
    "geology_usgs_puerto_rico": (10, 322, 459),
    "geology_ga_1m": (10, 921, 627),
    "geology_gsj_200k": (10, 907, 402),
}


@pytest.mark.network
@pytest.mark.parametrize("source", basemap_providers.GEOLOGY_SOURCES)
def test_shipped_source_serves_a_tile(
    source: str, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    monkeypatch.delenv("BASEMAP_TILE_URL", raising=False)
    z, x, y = KNOWN_TILES[source]
    content = basemap_tiles.fetch_tiles(source, basemap_tiles.TileRange(z, x, x, y, y))[(x, y)]
    assert content is not None
    assert not basemap_tiles.is_empty(content, "transparent")

from __future__ import annotations

# Standard library imports
import json
import math
from typing import TYPE_CHECKING

# Third party imports
import pytest

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

"""The native file of an import is saved in background, after the route answered."""

from __future__ import annotations

# Standard library imports
import contextlib
import logging
import threading
import time
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

# Third party imports
import pytest
from opengeodeweb_microservice.database import connection
from werkzeug.exceptions import HTTPException

# Local application imports
from opengeodeweb_back import geode_functions, test_utils, utils_functions
from opengeodeweb_back.geode_objects.geode_triangulated_surface3d import (
    GeodeTriangulatedSurface3D,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Generator

    from flask.testing import FlaskClient
    from werkzeug.test import TestResponse

    from opengeodeweb_back.geode_objects.geode_object import GeodeObject

GEODE_OBJECT_TYPE = "TriangulatedSurface3D"
FILENAME = "test.og_tsf3d"
NATIVE_FILE = "native.og_tsf3d"
ASSIGN_ROUTE = "/opengeodeweb_back/crs/assign_geographic"
LAMBERT = {"authority": "EPSG", "code": "2154", "name": "RGF93 v1 / Lambert-93"}
SAVE_ROUTE = "/opengeodeweb_back/save_viewable_file"
EXPORT_ROUTE = "/opengeodeweb_back/export_project"
BASEMAP_BUILD_ROUTE = "/opengeodeweb_back/basemap/build"
BASEMAP_DELETE_ROUTE = "/opengeodeweb_back/basemap/delete"
ROUTE_TIMEOUT = 10.0
# Larger than ROUTE_TIMEOUT: a blocked route fails the test before the save gives up
TIMEOUT = 25.0
STILL_RUNNING_DELAY = 0.5


@dataclass
class NativeSave:
    """Blocks every native save of a TriangulatedSurface3D until released."""

    release: threading.Event = field(default_factory=threading.Event)
    condition: threading.Condition = field(default_factory=threading.Condition)
    entered: int = 0
    error: Exception | None = None
    # How many saves fail with error, every one if None
    failures: int | None = None
    # Seconds a released save stays in progress, to widen the window of a write race
    hold: float = 0.0
    active: int = 0
    max_active: int = 0
    threads: list[threading.Thread] = field(default_factory=list)

    def wait_entered(self, count: int) -> bool:
        with self.condition:
            return self.condition.wait_for(lambda: self.entered >= count, TIMEOUT)


@dataclass
class Background[T]:
    """A call running in a thread, whose result is awaited with a timeout."""

    thread: threading.Thread
    outcome: dict[str, Any] = field(default_factory=dict)

    def is_running_after(self, delay: float) -> bool:
        self.thread.join(delay)
        return self.thread.is_alive()

    def result(self, timeout: float = ROUTE_TIMEOUT) -> T:
        self.thread.join(timeout)
        if self.thread.is_alive():
            pytest.fail(f"still running after {timeout}s")
        if "error" in self.outcome:
            raise self.outcome["error"]
        value: T = self.outcome["value"]
        return value


def _close_thread_session() -> None:
    registry = connection._state.scoped_session_registry  # noqa: SLF001
    if registry is not None:
        registry.remove()


@pytest.fixture
def native_save(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> Generator[NativeSave]:
    state = NativeSave()
    original_save = GeodeTriangulatedSurface3D.save

    def blocked_save(self: GeodeTriangulatedSurface3D, filename: str) -> list[str]:
        with state.condition:
            state.entered += 1
            state.condition.notify_all()
        if not state.release.wait(TIMEOUT):
            msg = "native save never released"
            raise TimeoutError(msg)
        with state.condition:
            failing = state.error is not None and state.failures != 0
            if failing and state.failures is not None:
                state.failures -= 1
            state.active += 1
            state.max_active = max(state.max_active, state.active)
        try:
            time.sleep(state.hold)
            if failing and state.error is not None:
                raise state.error
            return original_save(self, filename)
        finally:
            with state.condition:
                state.active -= 1

    monkeypatch.setattr(GeodeTriangulatedSurface3D, "save", blocked_save)
    test_utils.check_upload_file(client, FILENAME)
    try:
        yield state
    finally:
        state.release.set()
        for thread in state.threads:
            thread.join(TIMEOUT)
        # No pending nor failed native save may leak into the next test
        with client.application.app_context(), contextlib.suppress(HTTPException):
            utils_functions.wait_all_native_saved()
        utils_functions._native_saves.clear()  # noqa: SLF001


def _in_thread[T](state: NativeSave, function: Callable[[], T]) -> Background[T]:
    outcome: dict[str, Any] = {}

    def run() -> None:
        try:
            outcome["value"] = function()
        except BaseException as error:  # noqa: BLE001
            outcome["error"] = error
        finally:
            _close_thread_session()

    thread = threading.Thread(target=run, daemon=True)
    state.threads.append(thread)
    thread.start()
    return Background(thread, outcome)


def _import(client: FlaskClient, state: NativeSave) -> Background[TestResponse]:
    return _in_thread(
        state,
        lambda: client.post(
            SAVE_ROUTE,
            json={"geode_object_type": GEODE_OBJECT_TYPE, "filename": FILENAME},
        ),
    )


def _imported_item(client: FlaskClient, state: NativeSave) -> dict[str, Any]:
    """Import while the native save is blocked: the route must answer anyway."""
    response = _import(client, state).result()
    assert response.status_code == 200, response.get_json()
    item: dict[str, Any] = response.get_json()["data"][0]
    assert len(response.get_json()["data"]) == 1
    assert item["native_file"] == NATIVE_FILE
    return item


def _load_in_app(client: FlaskClient, data_id: str) -> GeodeObject:
    with client.application.app_context():
        return geode_functions.load_geode_object(data_id)


def test_route_answers_before_native_save(client: FlaskClient, native_save: NativeSave) -> None:
    """(a) save_viewable_file answers while the native save is still blocked."""
    item = _imported_item(client, native_save)
    assert not native_save.release.is_set()
    assert native_save.wait_entered(1)
    assert isinstance(item["binary_light_viewable"], str)


def test_native_file_saved_after_wait(client: FlaskClient, native_save: NativeSave) -> None:
    """(b) After wait_native_saved, the native file exists and loads."""
    item = _imported_item(client, native_save)
    native_save.release.set()
    with client.application.app_context():
        utils_functions.wait_native_saved(item["id"])
        native_path = Path(geode_functions.data_file_path(item["id"], NATIVE_FILE))
        assert native_path.is_file()
        GeodeTriangulatedSurface3D.load_one(str(native_path))
        assert isinstance(geode_functions.load_geode_object(item["id"]), GeodeTriangulatedSurface3D)


def test_load_waits_for_native_save(client: FlaskClient, native_save: NativeSave) -> None:
    """(c) load_geode_object does not return before the native save is done."""
    item = _imported_item(client, native_save)
    load = _in_thread(native_save, lambda: _load_in_app(client, item["id"]))
    assert load.is_running_after(STILL_RUNNING_DELAY), "load returned before the native save"
    native_save.release.set()
    assert isinstance(load.result(), GeodeTriangulatedSurface3D)


def test_failed_native_save_aborts_load(
    client: FlaskClient, native_save: NativeSave, caplog: pytest.LogCaptureFixture
) -> None:
    """(d) A failed native save makes load_geode_object abort with 500, and is logged."""
    native_save.error = RuntimeError("disk exploded")
    item = _imported_item(client, native_save)
    with caplog.at_level(logging.ERROR):
        native_save.release.set()
        # The error must be logged by wait_native_saved on the calling thread,
        # not from a done-callback: caplog only sees it reliably there.
        with pytest.raises(HTTPException) as error:
            _load_in_app(client, item["id"])
    assert error.value.code == 500
    assert "could not be saved" in str(error.value.description)
    assert "disk exploded" in caplog.text
    # A failed save keeps failing the same way
    with pytest.raises(HTTPException) as error:
        _load_in_app(client, item["id"])
    assert error.value.code == 500


def test_concurrent_imports_save_in_parallel(client: FlaskClient, native_save: NativeSave) -> None:
    """(e) Two imports issued concurrently run their native saves in parallel."""
    first = _import(client, native_save)
    second = _import(client, native_save)
    for import_call in (first, second):
        assert import_call.result().status_code == 200
    assert native_save.wait_entered(2), "both native saves should run at once"
    native_save.release.set()
    with client.application.app_context():
        utils_functions.wait_all_native_saved()


def test_export_contains_pending_native_file(
    client: FlaskClient, native_save: NativeSave, tmp_path: Path
) -> None:
    """(f) export_project waits for pending native saves and exports their files."""
    item = _imported_item(client, native_save)
    filename = "background_native_save.vease"
    export = _in_thread(
        native_save,
        lambda: client.post(EXPORT_ROUTE, json={"snapshot": {}, "filename": filename}),
    )
    assert export.is_running_after(STILL_RUNNING_DELAY), "export did not wait for the save"
    native_save.release.set()
    response = export.result()
    assert response.status_code == 200
    response.direct_passthrough = False
    vease = tmp_path / filename
    vease.write_bytes(response.get_data())
    response.close()
    (Path(client.application.config["DATA_FOLDER_PATH"]) / filename).unlink(missing_ok=True)
    with zipfile.ZipFile(vease) as zip_file:
        native_bytes = zip_file.read(f"{item['id']}/{NATIVE_FILE}")
    native_copy = tmp_path / NATIVE_FILE
    native_copy.write_bytes(native_bytes)
    GeodeTriangulatedSurface3D.load_one(str(native_copy))


def test_crs_assignment_waits_for_native_save(client: FlaskClient, native_save: NativeSave) -> None:
    """(g) A CRS assignment waits for the native save, then its change is in the final file."""
    item = _imported_item(client, native_save)
    assign = _in_thread(
        native_save,
        lambda: client.post(ASSIGN_ROUTE, json={"id": item["id"], **LAMBERT}),
    )
    assert assign.is_running_after(STILL_RUNNING_DELAY), (
        "assignment did not wait for the native save"
    )
    native_save.release.set()
    response = assign.result()
    assert response.status_code == 200, response.get_json()
    with client.application.app_context():
        utils_functions.wait_all_native_saved()
        geode_object = _load_in_app(client, item["id"])
    assert isinstance(geode_object, GeodeTriangulatedSurface3D)
    manager = geode_object.crs_manager()
    assert manager.active_coordinate_reference_system_name() == "EPSG:2154"


def _test_surface() -> GeodeTriangulatedSurface3D:
    return GeodeTriangulatedSurface3D.load_one(str(Path(__file__).parent / "data" / FILENAME))


def _wait_registered_save(data_id: str) -> None:
    """Wait for the background save of data_id to end, without settling it."""
    with utils_functions._native_saves_lock:  # noqa: SLF001
        entry = utils_functions._native_saves.get(data_id)  # noqa: SLF001
    if entry is not None:
        entry.future.exception(TIMEOUT)


def test_failed_native_save_is_retried(client: FlaskClient, native_save: NativeSave) -> None:
    """A failed background save is retried once by the next load, which then succeeds."""
    native_save.error = RuntimeError("transient lock")
    native_save.failures = 1
    item = _imported_item(client, native_save)
    native_save.release.set()
    _wait_registered_save(item["id"])
    assert native_save.failures == 0, "the background save should have failed"
    response = client.post(ASSIGN_ROUTE, json={"id": item["id"], **LAMBERT})
    assert response.status_code == 200, response.get_json()
    with client.application.app_context():
        utils_functions.wait_all_native_saved()
    assert isinstance(_load_in_app(client, item["id"]), GeodeTriangulatedSurface3D)


def test_failed_native_save_retry_fails(client: FlaskClient, native_save: NativeSave) -> None:
    """When the retry fails too, the load answers 500, and the next call retries again."""
    native_save.error = RuntimeError("disk exploded")
    native_save.failures = 2
    item = _imported_item(client, native_save)
    native_save.release.set()
    response = client.post(ASSIGN_ROUTE, json={"id": item["id"], **LAMBERT})
    assert response.status_code == 500
    assert "disk exploded" in response.get_json()["description"]
    assert native_save.failures == 0
    # The data is not lost for the session: the next call retries and heals it
    response = client.post(ASSIGN_ROUTE, json={"id": item["id"], **LAMBERT})
    assert response.status_code == 200, response.get_json()


def test_export_names_every_failed_native_save(
    client: FlaskClient, native_save: NativeSave, tmp_path: Path
) -> None:
    """export_project waits for every save, then answers 500 naming each failed data."""
    native_save.error = RuntimeError("disk exploded")
    item = _imported_item(client, native_save)
    other_id = "other-failing-data"
    utils_functions._save_native_in_background(  # noqa: SLF001
        _test_surface(), other_id, str(tmp_path / NATIVE_FILE)
    )
    native_save.release.set()
    response = client.post(
        EXPORT_ROUTE, json={"snapshot": {}, "filename": "failed_native_save.vease"}
    )
    assert response.status_code == 500
    description = response.get_json()["description"]
    assert item["id"] in description
    assert other_id in description


def test_resaves_of_one_data_never_overlap(client: FlaskClient, native_save: NativeSave) -> None:
    """Two re-saves of one data, requested at once, write its native file one at a time."""
    item = _imported_item(client, native_save)
    with client.application.app_context():
        native_path = geode_functions.data_file_path(item["id"], NATIVE_FILE)
    geode_object = _test_surface()
    start = threading.Barrier(2)

    def resave() -> None:
        start.wait(TIMEOUT)
        utils_functions._save_native_in_background(  # noqa: SLF001
            geode_object, item["id"], native_path
        )

    resaves = [_in_thread(native_save, resave) for _ in range(2)]
    for call in resaves:
        call.result()
    native_save.hold = 0.2
    native_save.release.set()
    with client.application.app_context():
        utils_functions.wait_native_saved(item["id"])
    assert native_save.entered == 3
    assert native_save.max_active == 1


def test_basemap_delete_waits_for_native_save(
    client: FlaskClient,
    native_save: NativeSave,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Deleting a basemap whose native save is pending waits for it, then removes it all."""
    any_tile = Path(__file__).parent / "data" / "basemap_tiles" / "1" / "0" / "0.png"
    monkeypatch.setenv("BASEMAP_TILE_URL", any_tile.as_uri())
    monkeypatch.setenv("BASEMAP_CACHE_FOLDER", str(tmp_path))
    build = client.post(
        BASEMAP_BUILD_ROUTE,
        json={
            "maps": ["satellite"],
            "bounds": {
                "x_min": 650_000.0,
                "y_min": 6_860_000.0,
                "x_max": 655_000.0,
                "y_max": 6_865_000.0,
            },
            "crs": LAMBERT,
            "z": 0.0,
        },
    )
    assert build.status_code == 200, build.get_json()
    data_id = build.get_json()["id"]
    with client.application.app_context():
        folder = Path(geode_functions.data_file_path(data_id))
    delete = _in_thread(
        native_save, lambda: client.post(BASEMAP_DELETE_ROUTE, json={"id": data_id})
    )
    assert delete.is_running_after(STILL_RUNNING_DELAY), "delete did not wait for the native save"
    native_save.release.set()
    response = delete.result()
    assert response.status_code == 200, response.get_json()
    assert not folder.exists()
    with utils_functions._native_saves_lock:  # noqa: SLF001
        assert data_id not in utils_functions._native_saves  # noqa: SLF001

from __future__ import annotations

# Standard library imports
import queue
import threading
import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flask.testing import FlaskClient

CHUNK_TIMEOUT_SECONDS = 2.0
LISTENERS_CONNECT_SECONDS = 0.5


# Opens a new event stream and reads its first chunk in a daemon thread: the test client
# Already reads that chunk inside client.get, which blocks until something is published.
def _read_next_chunk(client: FlaskClient) -> queue.Queue[bytes]:
    result: queue.Queue[bytes] = queue.Queue()

    def read() -> None:
        result.put(next(client.get("/events").iter_encoded()))

    threading.Thread(target=read, daemon=True).start()
    return result


def _chunk(result: queue.Queue[bytes]) -> str | None:
    try:
        return result.get(timeout=CHUNK_TIMEOUT_SECONDS).decode()
    except queue.Empty:
        return None


def test_every_listener_receives_each_event(client: FlaskClient) -> None:
    # A listener left over from a dropped connection must not take events meant for the others
    first = _read_next_chunk(client)
    second = _read_next_chunk(client)
    time.sleep(LISTENERS_CONNECT_SECONDS)
    client.get("/health", headers={"Accept": "text/event-stream"})
    assert _chunk(first) == "event: health\ndata: {}\n\n"
    assert _chunk(second) == "event: health\ndata: {}\n\n"


def test_stream_closes_once_server_timed_out(client: FlaskClient) -> None:
    # A stream left open would keep the cloud instance (and its billing) alive until the
    # Request timeout, long after the server stopped answering its health check
    app = client.application
    timeout_keys = ("MINUTES_BEFORE_TIMEOUT", "LAST_PING_TIME")
    saved = {key: app.config[key] for key in timeout_keys if key in app.config}
    app.config["EVENTS_KEEP_ALIVE_SECONDS"] = 0.1
    app.config["MINUTES_BEFORE_TIMEOUT"] = "1"
    app.config["LAST_PING_TIME"] = 0
    finished = threading.Event()

    def read_all() -> None:
        for _ in client.get("/events").iter_encoded():
            pass
        finished.set()

    try:
        threading.Thread(target=read_all, daemon=True).start()
        assert finished.wait(timeout=CHUNK_TIMEOUT_SECONDS)
    finally:
        app.config.pop("EVENTS_KEEP_ALIVE_SECONDS")
        for key in timeout_keys:
            app.config.pop(key, None)
        app.config.update(saved)


def test_idle_stream_sends_keep_alive(client: FlaskClient) -> None:
    app = client.application
    app.config["EVENTS_KEEP_ALIVE_SECONDS"] = 0.1
    try:
        assert _chunk(_read_next_chunk(client)) == ": keep-alive\n\n"
    finally:
        app.config.pop("EVENTS_KEEP_ALIVE_SECONDS")

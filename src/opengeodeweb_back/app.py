"""Packages"""

from __future__ import annotations

import argparse
import json
import logging
import queue
from pathlib import Path
from typing import TYPE_CHECKING, Any

import flask
import flask_cors  # type: ignore[import-untyped]
from flask import Flask, Response
from flask_cors import cross_origin
from opengeodeweb_microservice.database import connection
from werkzeug.exceptions import HTTPException

from opengeodeweb_back import app_config, utils_functions
from opengeodeweb_back.routes import blueprint_routes
from opengeodeweb_back.routes.create import blueprint_create

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)


def _register_request_hooks(app: flask.Flask) -> None:
    @app.before_request
    def before_request() -> flask.Response | None:
        if flask.request.method == "OPTIONS":
            response = flask.make_response()
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,PUT,DELETE,OPTIONS"
            return response
        utils_functions.before_request(flask.current_app)
        return None

    @app.teardown_request
    def teardown_request(exception: BaseException | None) -> None:
        utils_functions.teardown_request(flask.current_app, exception)


def _register_event_stream(app: flask.Flask) -> None:
    def wants_event_stream() -> bool:
        accept = flask.request.headers.get("Accept", "")
        return "text/event-stream" in accept

    _event_queue: queue.Queue[tuple[str, dict[str, Any]]] = queue.Queue()

    def publish_event(event: str, data: dict[str, Any]) -> None:
        _event_queue.put((event, data))

    def stream_events() -> Generator[str]:
        while True:
            event, data = _event_queue.get()
            yield f"event: {event}\ndata: {json.dumps(data)}\n\n"

    @app.after_request
    def after_request(response: flask.Response) -> flask.Response:
        endpoint = flask.request.endpoint.replace(".", "/") if flask.request.endpoint else None
        if endpoint in {"events", None}:
            return response

        if wants_event_stream():
            payload: dict[str, Any]
            try:
                payload = response.get_json()
            except ValueError:
                payload = {"status": response.status_code}
            publish_event(endpoint, payload)
        return response

    @app.route("/events")
    def events() -> flask.Response:
        return flask.Response(stream_events(), mimetype="text/event-stream")


def _register_error_handlers(app: flask.Flask) -> None:
    @app.errorhandler(HTTPException)
    def errorhandler(exception: HTTPException) -> tuple[dict[str, Any], int] | Response:
        return utils_functions.handle_exception(exception)

    @app.errorhandler(Exception)
    def handle_generic_exception(exception: Exception) -> Response:
        return utils_functions.handle_unexpected_exception(exception)


def _register_base_routes(app: flask.Flask) -> None:
    @app.route(
        "/error",
        methods=["POST"],
    )
    def return_error() -> Response:
        flask.abort(500, "Test")
        return flask.make_response({}, 500)

    @app.route(
        "/health",
        methods=["GET"],
    )
    def health() -> Response:
        if utils_functions.kill_task(flask.current_app):
            return flask.make_response({}, 500)
        return flask.make_response({}, 200)

    @app.route("/", methods=["POST"])
    @cross_origin()
    def root() -> Response:
        return flask.make_response({}, 200)


def create_app(name: str) -> flask.Flask:
    app = flask.Flask(name)
    _register_request_hooks(app)
    _register_event_stream(app)
    _register_error_handlers(app)
    _register_base_routes(app)
    return app


def register_ogw_back_blueprints(app: flask.Flask) -> None:
    app.register_blueprint(
        blueprint_routes.routes,
        url_prefix="/opengeodeweb_back",
        name="opengeodeweb_back",
    )
    app.register_blueprint(
        blueprint_create.routes,
        url_prefix="/opengeodeweb_back/create",
        name="opengeodeweb_create",
    )


def run_server(app: Flask) -> None:
    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("-d", "--debug", action="store_true", default=False)
    pre_parser.add_argument("-pfp", "--project_folder_path", type=str)
    pre_args, _ = pre_parser.parse_known_args()

    if pre_args.project_folder_path is None:
        msg = "project_folder_path must be provided"
        raise ValueError(msg)
    project_folder_path = str(Path(pre_args.project_folder_path).resolve())

    if pre_args.debug:
        app.config.from_object(app_config.DevConfig(project_folder_path))
    else:
        app.config.from_object(app_config.ProdConfig(project_folder_path))

    parser = argparse.ArgumentParser(
        prog="OpenGeodeWeb-Back", description="Backend server for OpenGeodeWeb"
    )
    parser.add_argument("--host", default=app.config.get("HOST"), type=str, help="Host to run on")
    parser.add_argument(
        "-p",
        "--port",
        default=app.config.get("PORT"),
        type=str,
        help="Port to listen on",
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=pre_args.debug,
        action="store_true",
        help="Whether to run in debug mode",
    )
    parser.add_argument(
        "-pfp",
        "--project_folder_path",
        default=project_folder_path,
        type=str,
        help="Path to the folder where the project is stored",
    )
    parser.add_argument(
        "-dfp",
        "--data_folder_path",
        default=app.config.get("DATA_FOLDER_PATH"),
        type=str,
        help="Path to the folder where the data is stored",
    )
    parser.add_argument(
        "-ufp",
        "--upload_folder_path",
        default=app.config.get("UPLOAD_FOLDER_PATH"),
        type=str,
        help="Path to the folder where uploads are stored",
    )
    parser.add_argument(
        "-origins",
        "--allowed_origins",
        default=app.config.get("ORIGINS"),
        nargs="+",
        help="Origins that are allowed to connect to the server",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        default=app.config.get("MINUTES_BEFORE_TIMEOUT"),
        type=int,
        help="Number of minutes before the server times out",
    )
    args = parser.parse_args()

    args.project_folder_path = str(Path(args.project_folder_path).resolve())

    logging.basicConfig(
        level=logging.DEBUG if args.debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("Arguments: %s", args)

    app.config.update(
        HOST=args.host,
        PORT=args.port,
        FLASK_DEBUG=args.debug,
        PROJECT_FOLDER_PATH=args.project_folder_path,
        DATA_FOLDER_PATH=args.data_folder_path,
        UPLOAD_FOLDER_PATH=args.upload_folder_path,
        ALLOWED_ORIGINS=args.allowed_origins,
        MINUTES_BEFORE_TIMEOUT=args.timeout,
    )

    db_filename = app.config.get("DATABASE_FILENAME")
    if not isinstance(db_filename, str):
        msg = f"DATABASE_FILENAME config must be a string, got {db_filename!r}"
        raise TypeError(msg)
    db_path = Path(str(app.config.get("DATA_FOLDER_PATH"))) / db_filename
    db_path.parent.mkdir(parents=True, exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    connection.init_database(db_path)
    logger.info("Database initialized at: %s", db_path)

    flask_cors.CORS(app, origins=args.allowed_origins)
    app.run(
        debug=app.config.get("FLASK_DEBUG"),
        host=app.config.get("HOST"),
        port=app.config.get("PORT"),
        ssl_context=app.config.get("SSL"),
    )


def run_opengeodeweb_back() -> None:
    app = create_app(__name__)
    register_ogw_back_blueprints(app)
    run_server(app)
    logger.info("Server stopped")


# ''' Main '''
if __name__ == "__main__":
    run_opengeodeweb_back()

"""Packages"""

import argparse
import os
from threading import Timer
from typing import Any
import flask
import flask_cors  # type: ignore
from flask import Flask, Response
from flask_cors import cross_origin
from werkzeug.exceptions import HTTPException
from opengeodeweb_back import utils_functions, app_config
from opengeodeweb_back.routes import blueprint_routes
from opengeodeweb_back.routes.create import blueprint_create
from opengeodeweb_microservice.database import connection


def create_app(name: str) -> flask.Flask:
    app = flask.Flask(name)

    @app.before_request
    def before_request() -> flask.Response | None:
        if flask.request.method == "OPTIONS":
            response = flask.make_response()
            response.headers["Access-Control-Allow-Methods"] = (
                "GET,POST,PUT,DELETE,OPTIONS"
            )
            return response
        utils_functions.before_request(flask.current_app)
        return None

    @app.teardown_request
    def teardown_request(exception: BaseException | None) -> None:
        utils_functions.teardown_request(flask.current_app, exception)

    @app.errorhandler(HTTPException)
    def errorhandler(exception: HTTPException) -> tuple[dict[str, Any], int] | Response:
        return utils_functions.handle_exception(exception)

    @app.errorhandler(Exception)
    def handle_generic_exception(exception: Exception) -> Response:
        print("\033[91mError:\033[0m \033[91m" + str(exception) + "\033[0m", flush=True)
        return flask.make_response({"description": str(exception)}, 500)

    @app.route(
        "/error",
        methods=["POST"],
    )
    def return_error() -> Response:
        flask.abort(500, f"Test")
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

    @app.route("/kill", methods=["POST"])
    @cross_origin()
    def kill() -> None:
        print("Manual server kill, shutting down...", flush=True)
        Timer(1.5, os._exit, [0]).start()

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
    parser = argparse.ArgumentParser(
        prog="OpenGeodeWeb-Back", description="Backend server for OpenGeodeWeb"
    )
    parser.add_argument(
        "--host",
        type=str,
        help="Host to run on",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=str,
        help="Port to listen on",
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=app.config.get("FLASK_DEBUG"),
        help="Whether to run in debug mode",
        action="store_true",
    )
    parser.add_argument(
        "-pfp",
        "--project_folder_path",
        type=str,
        help="Path to the folder where the project is stored",
    )
    parser.add_argument(
        "-dfp",
        "--data_folder_path",
        type=str,
        help="Path to the folder where the data is stored",
    )
    parser.add_argument(
        "-ufp",
        "--upload_folder_path",
        type=str,
        help="Path to the folder where uploads are stored",
    )
    parser.add_argument(
        "-origins",
        "--allowed_origins",
        nargs="+",
        help="Origins that are allowed to connect to the server",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        help="Number of minutes before the server times out",
    )
    args, _ = parser.parse_known_args()

    if args.project_folder_path is None:
        raise ValueError("project_folder_path must be provided")
    else:
        args.project_folder_path = os.path.abspath(args.project_folder_path)

    if args.debug:
        app.config.from_object(app_config.DevConfig(args.project_folder_path))
    else:
        app.config.from_object(app_config.ProdConfig(args.project_folder_path))

    print(app.config, flush=True)
    if args.host is not None:
        app.config.update(HOST=args.host)
    else:
        args.host = app.config.get("HOST")

    if args.port is not None:
        app.config.update(PORT=args.port)
    else:
        args.port = app.config.get("PORT")

    if args.debug is not None:
        app.config.update(FLASK_DEBUG=args.debug)
    else:
        args.debug = app.config.get("FLASK_DEBUG")

    if args.data_folder_path is not None:
        app.config.update(DATA_FOLDER_PATH=args.data_folder_path)
    else:
        args.data_folder_path = app.config.get("DATA_FOLDER_PATH")

    if args.upload_folder_path is not None:
        app.config.update(UPLOAD_FOLDER_PATH=args.upload_folder_path)
    else:
        args.upload_folder_path = app.config.get("UPLOAD_FOLDER_PATH")

    if args.allowed_origins is not None:
        app.config.update(ALLOWED_ORIGINS=args.allowed_origins)
    else:
        args.allowed_origins = app.config.get("ALLOWED_ORIGINS")

    if args.timeout is not None:
        app.config.update(MINUTES_BEFORE_TIMEOUT=args.timeout)
    else:
        args.timeout = app.config.get("MINUTES_BEFORE_TIMEOUT")

    print(f"{args=}", flush=True)

    db_filename = app.config.get("DATABASE_FILENAME")
    if not isinstance(db_filename, str):
        raise TypeError(
            f"DATABASE_FILENAME config must be a string, got {db_filename!r}"
        )
    db_path = os.path.join(str(app.config.get("DATA_FOLDER_PATH")), db_filename)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    connection.init_database(db_path)
    print(f"Database initialized at: {db_path}", flush=True)
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
    print("Server stopped", flush=True)


# ''' Main '''
if __name__ == "__main__":
    run_opengeodeweb_back()

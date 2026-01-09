"""Packages"""

import argparse
import os
from typing import Any
import flask
import flask_cors  # type: ignore
from flask import Flask, Response
from flask_cors import cross_origin
from werkzeug.exceptions import HTTPException
from opengeodeweb_back import utils_functions, app_config
from opengeodeweb_back.routes import blueprint_routes
from opengeodeweb_back.routes.models import blueprint_models
from opengeodeweb_back.routes.create import blueprint_create
from opengeodeweb_microservice.database import connection


def create_app(name: str) -> flask.Flask:
    app = flask.Flask(name)

    """ Config variables """
    FLASK_DEBUG = (
        True if os.environ.get("FLASK_DEBUG", default=None) == "True" else False
    )
    if FLASK_DEBUG == False:
        app.config.from_object(app_config.ProdConfig)
    else:
        app.config.from_object(app_config.DevConfig)

    if FLASK_DEBUG == False:
        SECONDS_BETWEEN_SHUTDOWNS: float = float(
            app.config.get("SECONDS_BETWEEN_SHUTDOWNS") or 60.0
        )
        utils_functions.set_interval(
            utils_functions.kill_task, SECONDS_BETWEEN_SHUTDOWNS, app
        )

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

    @app.route("/", methods=["POST"])
    @cross_origin()
    def root() -> Response:
        return flask.make_response({}, 200)

    @app.route("/kill", methods=["POST"])
    @cross_origin()
    def kill() -> None:
        print("Manual server kill, shutting down...", flush=True)
        os._exit(0)

    return app


def register_ogw_back_blueprints(app: flask.Flask) -> None:
    app.register_blueprint(
        blueprint_routes.routes,
        url_prefix="/opengeodeweb_back",
        name="opengeodeweb_back",
    )
    app.register_blueprint(
        blueprint_models.routes,
        url_prefix="/opengeodeweb_back/models",
        name="opengeodeweb_models",
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
        default=app.config.get("DEFAULT_HOST"),
        help="Host to run on",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=app.config.get("DEFAULT_PORT"),
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
        "-dfp",
        "--data_folder_path",
        type=str,
        default=app.config.get("DEFAULT_DATA_FOLDER_PATH"),
        help="Path to the folder where data is stored",
    )
    parser.add_argument(
        "-ufp",
        "--upload_folder_path",
        type=str,
        default=app.config.get("DEFAULT_DATA_FOLDER_PATH"),
        help="Path to the folder where uploads are stored",
    )
    parser.add_argument(
        "-origins",
        "--allowed_origins",
        default=app.config.get("ORIGINS"),
        help="Origins that are allowed to connect to the server",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        default=app.config.get("MINUTES_BEFORE_TIMEOUT"),
        help="Number of minutes before the server times out",
    )
    args = parser.parse_args()
    app.config.update(DATA_FOLDER_PATH=args.data_folder_path)
    app.config.update(
        EXTENSIONS_FOLDER_PATH=os.path.join(str(args.data_folder_path), "extensions")
    )
    app.config.update(UPLOAD_FOLDER=args.upload_folder_path)
    app.config.update(MINUTES_BEFORE_TIMEOUT=args.timeout)
    flask_cors.CORS(app, origins=args.allowed_origins)
    print(
        f"Host: {args.host}, Port: {args.port}, Debug: {args.debug}, "
        f"Data folder path: {args.data_folder_path}, Timeout: {args.timeout}, "
        f"Origins: {args.allowed_origins}",
        flush=True,
    )

    db_filename: str = app.config.get("DATABASE_FILENAME") or "project.db"
    db_path = os.path.join(str(args.data_folder_path), db_filename)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    connection.init_database(db_path)
    print(f"Database initialized at: {db_path}", flush=True)
    app.run(
        debug=args.debug,
        host=args.host,
        port=args.port,
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

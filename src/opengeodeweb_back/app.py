"""Packages"""

import argparse
import os
import time
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

""" Global config """
app: Flask = flask.Flask(__name__)

""" Config variables """
FLASK_DEBUG = True if os.environ.get("FLASK_DEBUG", default=None) == "True" else False
if FLASK_DEBUG == False:
    app.config.from_object(app_config.ProdConfig)
else:
    app.config.from_object(app_config.DevConfig)
DEFAULT_HOST: str = app.config.get("DEFAULT_HOST") or "localhost"
DEFAULT_PORT: int = int(app.config.get("DEFAULT_PORT") or 5000)
DEFAULT_DATA_FOLDER_PATH: str = app.config.get("DEFAULT_DATA_FOLDER_PATH") or "./data"
ORIGINS: Any = app.config.get("ORIGINS")
TIMEOUT: int = int(app.config.get("MINUTES_BEFORE_TIMEOUT") or 30)
SSL: Any = app.config.get("SSL")
SECONDS_BETWEEN_SHUTDOWNS: float = float(
    app.config.get("SECONDS_BETWEEN_SHUTDOWNS") or 60.0
)


@app.before_request
def before_request() -> None:
    utils_functions.before_request(flask.current_app)


@app.teardown_request
def teardown_request(exception: BaseException | None) -> None:
    utils_functions.teardown_request(flask.current_app, exception)


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

if FLASK_DEBUG == False:
    utils_functions.set_interval(
        utils_functions.kill_task, SECONDS_BETWEEN_SHUTDOWNS, app
    )


@app.errorhandler(HTTPException)
def errorhandler(e: HTTPException) -> tuple[dict[str, Any], int] | Response:
    return utils_functions.handle_exception(e)


@app.errorhandler(Exception)
def handle_generic_exception(e: Exception) -> Response:
    return flask.make_response({"error": str(e)}, 500)


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


def run_server() -> None:
    parser = argparse.ArgumentParser(
        prog="OpenGeodeWeb-Back", description="Backend server for OpenGeodeWeb"
    )
    parser.add_argument("--host", type=str, default=DEFAULT_HOST, help="Host to run on")
    parser.add_argument(
        "-p", "--port", type=int, default=DEFAULT_PORT, help="Port to listen on"
    )
    parser.add_argument(
        "-d",
        "--debug",
        default=FLASK_DEBUG,
        help="Whether to run in debug mode",
        action="store_true",
    )
    parser.add_argument(
        "-dfp",
        "--data_folder_path",
        type=str,
        default=DEFAULT_DATA_FOLDER_PATH,
        help="Path to the folder where data is stored",
    )
    parser.add_argument(
        "-ufp",
        "--upload_folder_path",
        type=str,
        default=DEFAULT_DATA_FOLDER_PATH,
        help="Path to the folder where uploads are stored",
    )
    parser.add_argument(
        "-origins",
        "--allowed_origins",
        default=ORIGINS,
        help="Origins that are allowed to connect to the server",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        default=TIMEOUT,
        help="Number of minutes before the server times out",
    )
    args = parser.parse_args()
    app.config.update(DATA_FOLDER_PATH=args.data_folder_path)
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
    db_path = os.path.join(args.data_folder_path, db_filename)
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    connection.init_database(db_path)
    print(f"Database initialized at: {db_path}", flush=True)
    app.run(debug=args.debug, host=args.host, port=args.port, ssl_context=SSL)


# ''' Main '''
if __name__ == "__main__":
    run_server()

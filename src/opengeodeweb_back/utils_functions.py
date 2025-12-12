# Standard library imports
import os
import threading
import time
import zipfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any


# Third party imports
import flask
import fastjsonschema  # type: ignore
import importlib.metadata as metadata
import shutil
from werkzeug.exceptions import HTTPException
import werkzeug
from opengeodeweb_microservice.schemas import SchemaDict
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session

# Local application imports
from . import geode_functions
from .geode_objects import geode_objects
from .geode_objects.types import GeodeObjectType
from .geode_objects.geode_object import GeodeObject


def increment_request_counter(current_app: flask.Flask) -> None:
    if "REQUEST_COUNTER" in current_app.config:
        REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER", 0))
        REQUEST_COUNTER += 1
        current_app.config.update(REQUEST_COUNTER=REQUEST_COUNTER)


def decrement_request_counter(current_app: flask.Flask) -> None:
    if "REQUEST_COUNTER" in current_app.config:
        REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER", 0))
        REQUEST_COUNTER -= 1
        current_app.config.update(REQUEST_COUNTER=REQUEST_COUNTER)


def update_last_request_time(current_app: flask.Flask) -> None:
    if "LAST_REQUEST_TIME" in current_app.config:
        LAST_REQUEST_TIME = time.time()
        current_app.config.update(LAST_REQUEST_TIME=LAST_REQUEST_TIME)


def terminate_session(exception: BaseException | None) -> None:
    session = flask.g.pop("session", None)
    if session is None:
        return
    if exception is None:
        session.commit()
    else:
        session.rollback()
    session.close()


def before_request(current_app: flask.Flask) -> None:
    increment_request_counter(current_app)
    flask.g.session = get_session()


def teardown_request(
    current_app: flask.Flask, exception: BaseException | None = None
) -> None:
    decrement_request_counter(current_app)
    update_last_request_time(current_app)
    terminate_session(exception)


def kill_task(current_app: flask.Flask) -> None:
    REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER", 0))
    LAST_PING_TIME = float(current_app.config.get("LAST_PING_TIME", 0))
    LAST_REQUEST_TIME = float(current_app.config.get("LAST_REQUEST_TIME", 0))
    MINUTES_BEFORE_TIMEOUT = float(current_app.config.get("MINUTES_BEFORE_TIMEOUT", 0))
    current_time = time.time()
    minutes_since_last_request = (current_time - LAST_REQUEST_TIME) / 60
    minutes_since_last_ping = (current_time - LAST_PING_TIME) / 60

    if REQUEST_COUNTER > 0:
        return
    if MINUTES_BEFORE_TIMEOUT == 0:
        return
    if minutes_since_last_ping > MINUTES_BEFORE_TIMEOUT:
        kill_server()
    if minutes_since_last_request > MINUTES_BEFORE_TIMEOUT:
        kill_server()


def kill_server() -> None:
    print("Server timed out due to inactivity, shutting down...", flush=True)
    os._exit(0)


def versions(list_packages: list[str]) -> list[dict[str, str]]:
    list_with_versions = []
    for package in list_packages:
        list_with_versions.append(
            {"package": package, "version": metadata.distribution(package).version}
        )
    return list_with_versions


def validate_request(request: flask.Request, schema: SchemaDict) -> dict[str, Any]:
    json_data = request.get_json(force=True, silent=True)

    if json_data is None:
        json_data = {}
    try:
        validate = fastjsonschema.compile(schema)
        validate(json_data)
    except fastjsonschema.JsonSchemaException as e:
        error_msg = str(e)
        print("Validation failed:", error_msg, flush=True)
        flask.abort(400, error_msg)
    return json_data


def set_interval(
    function: Callable[[flask.Flask], None], seconds: float, args: flask.Flask
) -> threading.Timer:
    def function_wrapper() -> None:
        set_interval(function, seconds, args)
        function(args)

    timer = threading.Timer(seconds, function_wrapper)
    timer.daemon = True
    timer.start()
    return timer


def extension_from_filename(filename: str) -> str:
    return os.path.splitext(filename)[1][1:]


def send_file(
    upload_folder: str, saved_files: list[str], new_file_name: str
) -> flask.Response:
    if len(saved_files) == 1:
        mimetype = "application/octet-binary"
    else:
        mimetype = "application/zip"
        new_file_name = os.path.splitext(new_file_name)[0] + ".zip"
        with zipfile.ZipFile(
            os.path.join(os.path.abspath(upload_folder), new_file_name), "w"
        ) as zipObj:
            for saved_file_path in saved_files:
                zipObj.write(
                    saved_file_path,
                    os.path.basename(saved_file_path),
                )

    response = flask.send_from_directory(
        directory=os.path.abspath(upload_folder),
        path=new_file_name,
        as_attachment=True,
        mimetype=mimetype,
    )
    response.headers["new-file-name"] = new_file_name
    response.headers["Access-Control-Expose-Headers"] = "new-file-name"

    return response


def handle_exception(exception: HTTPException) -> flask.Response:
    print("\033[91mError:\033[0m \033[91m" + str(exception) + "\033[0m", flush=True)
    response = flask.jsonify(
        {
            "code": exception.code,
            "name": exception.name,
            "description": exception.description or "An error occurred",
        }
    )
    response.content_type = "application/json"
    response.status_code = exception.code or 500
    return response


def create_data_folder_from_id(data_id: str) -> str:
    base_data_folder = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(base_data_folder, data_id)
    os.makedirs(data_path, exist_ok=True)
    return data_path


def save_all_viewables_and_return_info(
    geode_object: GeodeObject,
    data: Data,
    data_path: str,
) -> dict[str, str | list[str]]:
    with ThreadPoolExecutor() as executor:
        (native_files, viewable_path, light_path) = executor.map(
            lambda args: args[0](args[1]),
            [
                (
                    geode_object.save,
                    os.path.join(
                        data_path, "native." + geode_object.native_extension()
                    ),
                ),
                (geode_object.save_viewable, os.path.join(data_path, "viewable")),
                (
                    geode_object.save_light_viewable,
                    os.path.join(data_path, "light_viewable"),
                ),
            ],
        )
        with open(light_path, "rb") as f:
            binary_light_viewable = f.read()
        data.native_file = os.path.basename(native_files[0])
        data.viewable_file = os.path.basename(viewable_path)
        data.light_viewable_file = os.path.basename(light_path)

        if not data.input_file:
            data.input_file = data.native_file

        assert data.native_file is not None
        assert data.viewable_file is not None
        assert data.light_viewable_file is not None
        return {
            "native_file": data.native_file,
            "viewable_file": data.viewable_file,
            "id": data.id,
            "name": geode_object.identifier.name(),
            "viewer_type": data.viewer_object,
            "binary_light_viewable": binary_light_viewable.decode("utf-8"),
            "geode_object_type": data.geode_object,
            "input_file": data.input_file or "",
            "additional_files": data.additional_files or [],
        }


def generate_native_viewable_and_light_viewable_from_object(
    geode_object: GeodeObject,
) -> dict[str, str | list[str]]:
    data = Data.create(
        geode_object=geode_object.geode_object_type(),
        viewer_object=geode_object.viewer_type(),
    )
    data_path = create_data_folder_from_id(data.id)
    return save_all_viewables_and_return_info(geode_object, data, data_path)


def generate_native_viewable_and_light_viewable_from_file(
    geode_object_type: GeodeObjectType, input_file: str
) -> dict[str, str | list[str]]:
    generic_geode_object = geode_objects[geode_object_type]
    data = Data.create(
        geode_object=geode_object_type,
        viewer_object=generic_geode_object.viewer_type(),
        input_file=input_file,
    )

    data_path = create_data_folder_from_id(data.id)

    full_input_filename = geode_functions.upload_file_path(input_file)
    copied_full_path = os.path.join(
        data_path, werkzeug.utils.secure_filename(input_file)
    )
    shutil.copy2(full_input_filename, copied_full_path)

    additional_files_copied: list[str] = []
    additional = generic_geode_object.additional_files(full_input_filename)
    for additional_file in additional.mandatory_files + additional.optional_files:
        if additional_file.is_missing:
            continue
        source_path = os.path.join(
            os.path.dirname(full_input_filename), additional_file.filename
        )
        if not os.path.exists(source_path):
            continue
        dest_path = os.path.join(data_path, additional_file.filename)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copy2(source_path, dest_path)
        additional_files_copied.append(additional_file.filename)

    geode_object = generic_geode_object.load(copied_full_path)
    data.additional_files = additional_files_copied
    return save_all_viewables_and_return_info(
        geode_object,
        data,
        data_path,
    )

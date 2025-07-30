# Standard library imports
import os
import threading
import time
import uuid
import zipfile

# Third party imports
import flask
import fastjsonschema
import importlib.metadata as metadata

# Local application imports
from . import geode_functions


def increment_request_counter(current_app):
    if "REQUEST_COUNTER" in current_app.config:
        REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER"))
        REQUEST_COUNTER += 1
        current_app.config.update(REQUEST_COUNTER=REQUEST_COUNTER)


def decrement_request_counter(current_app):
    if "REQUEST_COUNTER" in current_app.config:
        REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER"))
        REQUEST_COUNTER -= 1
        current_app.config.update(REQUEST_COUNTER=REQUEST_COUNTER)


def update_last_request_time(current_app):
    if "LAST_REQUEST_TIME" in current_app.config:
        LAST_REQUEST_TIME = time.time()
        current_app.config.update(LAST_REQUEST_TIME=LAST_REQUEST_TIME)


def before_request(current_app):
    increment_request_counter(current_app)


def teardown_request(current_app):
    decrement_request_counter(current_app)
    update_last_request_time(current_app)


def kill_task(current_app):
    REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER"))
    LAST_PING_TIME = float(current_app.config.get("LAST_PING_TIME"))
    LAST_REQUEST_TIME = float(current_app.config.get("LAST_REQUEST_TIME"))
    MINUTES_BEFORE_TIMEOUT = float(current_app.config.get("MINUTES_BEFORE_TIMEOUT"))
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


def kill_server():
    print("Server timed out due to inactivity, shutting down...", flush=True)
    os._exit(0)


def versions(list_packages: list):
    list_with_versions = []
    for package in list_packages:
        list_with_versions.append(
            {"package": package, "version": metadata.distribution(package).version}
        )
    return list_with_versions


def validate_request(request, schema):
    json_data = request.get_json(force=True, silent=True)

    if json_data is None:
        json_data = {}

    try:
        validate = fastjsonschema.compile(schema)
        validate(json_data)
    except fastjsonschema.JsonSchemaException as e:
        error_msg = str(e)
        flask.abort(400, error_msg)


def set_interval(func, sec, args=None):
    def func_wrapper():
        set_interval(func, sec, args)
        func(args)

    t = threading.Timer(sec, func_wrapper)
    t.daemon = True
    t.start()
    return t


def extension_from_filename(filename):
    return os.path.splitext(filename)[1][1:]


def send_file(upload_folder, saved_files, new_file_name):
    if len(saved_files) == 1:
        mimetype = "application/octet-binary"
    else:
        mimetype = "application/zip"
        new_file_name = os.path.splitext(new_file_name)[0] + ".zip"
        with zipfile.ZipFile(os.path.join(upload_folder, new_file_name), "w") as zipObj:
            for saved_file_path in saved_files:
                zipObj.write(
                    saved_file_path,
                    os.path.basename(saved_file_path),
                )

    response = flask.send_from_directory(
        directory=upload_folder,
        path=new_file_name,
        as_attachment=True,
        mimetype=mimetype,
    )
    response.headers["new-file-name"] = new_file_name
    response.headers["Access-Control-Expose-Headers"] = "new-file-name"

    return response


def handle_exception(e):
    response = e.get_response()
    response.data = flask.json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


def generate_native_viewable_and_light_viewable(geode_object, data):
    generated_id = str(uuid.uuid4()).replace("-", "")
    DATA_FOLDER_PATH = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(DATA_FOLDER_PATH, generated_id)
    name = data.name()
    object_type = geode_functions.get_object_type(geode_object)

    saved_native_file_path = geode_functions.save(
        geode_object,
        data,
        data_path,
        "native." + data.native_extension(),
    )
    saved_viewable_file_path = geode_functions.save_viewable(
        geode_object, data, data_path, "viewable"
    )
    viewable_file_name = os.path.basename(saved_viewable_file_path)
    saved_light_viewable_file_path = geode_functions.save_light_viewable(
        geode_object, data, data_path, "light_viewable"
    )
    f = open(saved_light_viewable_file_path, "rb")
    binary_light_viewable = f.read()
    f.close()

    return {
        "name": name,
        "native_file_name": os.path.basename(saved_native_file_path[0]),
        "viewable_file_name": viewable_file_name,
        "id": generated_id,
        "object_type": object_type,
        "binary_light_viewable": str(binary_light_viewable, "utf-8"),
        "geode_object": geode_object,
    }

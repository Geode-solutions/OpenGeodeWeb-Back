# Standard library imports
import os
import threading
import time
import zipfile

# Third party imports
import flask
from jsonschema import validate
from jsonschema.exceptions import ValidationError
import pkg_resources

# Local application imports


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
    DESKTOP_APP = bool(current_app.config.get("DESKTOP_APP"))
    REQUEST_COUNTER = int(current_app.config.get("REQUEST_COUNTER"))
    LAST_PING_TIME = float(current_app.config.get("LAST_PING_TIME"))
    LAST_REQUEST_TIME = float(current_app.config.get("LAST_REQUEST_TIME"))
    MINUTES_BEFORE_TIMEOUT = float(current_app.config.get("MINUTES_BEFORE_TIMEOUT"))
    current_time = time.time()
    minutes_since_last_request = (current_time - LAST_REQUEST_TIME) / 60
    minutes_since_last_ping = (current_time - LAST_PING_TIME) / 60

    if (
        (
            (minutes_since_last_request > MINUTES_BEFORE_TIMEOUT)
            and (DESKTOP_APP == False)
        )
        or (minutes_since_last_ping > MINUTES_BEFORE_TIMEOUT)
    ) and (REQUEST_COUNTER == 0):
        print("Server timed out due to inactivity, shutting down...", flush=True)
        os._exit(0)


def versions(list_packages: list):
    list_with_versions = []
    for package in list_packages:
        list_with_versions.append(
            {
                "package": package,
                "version": pkg_resources.get_distribution(package).version,
            }
        )
    return list_with_versions


def validate_request(request, schema):
    json_data = request.get_json(force=True, silent=True)

    if json_data is None:
        json_data = {}

    try:
        validate(instance=json_data, schema=schema)
    except ValidationError as e:
        flask.abort(400, f"Validation error: {e.message}")


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

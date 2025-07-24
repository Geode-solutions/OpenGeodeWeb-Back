# Standard library imports
import re
import os

# Third party imports
import flask

# Local application imports
from src.opengeodeweb_back import geode_functions, utils_functions


def test_increment_request_counter(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.increment_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_decrement_request_counter(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.decrement_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0


def test_update_last_request_time(app_context):
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    utils_functions.update_last_request_time(flask.current_app)
    assert flask.current_app.config.get("LAST_REQUEST_TIME") >= LAST_REQUEST_TIME


def test_before_request(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.before_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_teardown_request(app_context):
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.teardown_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    assert flask.current_app.config.get("LAST_REQUEST_TIME") >= LAST_REQUEST_TIME


def test_versions():
    list_packages = [
        "OpenGeode-core",
        "OpenGeode-IO",
        "OpenGeode-Geosciences",
        "OpenGeode-GeosciencesIO",
    ]
    versions = utils_functions.versions(list_packages)
    assert type(versions) is list
    for version in versions:
        assert type(version) is dict


def test_extension_from_filename():
    extension = utils_functions.extension_from_filename("test.toto")
    assert type(extension) is str
    assert extension.count(".") == 0


def test_handle_exception(client):
    route = "/error"
    response = client.post(route)
    assert response.status_code == 500
    data = response.get_json()
    assert type(data) is dict
    assert type(data["description"]) is str
    assert type(data["name"]) is str
    assert type(data["code"]) is int


def test_generate_native_viewable_and_light_viewable():
    geode_object = "BRep"
    folder_absolute_path = os.path.abspath("./data")
    data = geode_functions.load(
        geode_object, os.path.join(folder_absolute_path, "test.og_brep")
    )
    if not os.path.isdir(folder_absolute_path):
        raise ValueError(f"Invalid folder path: {folder_absolute_path}")
    # folder_absolute_path = "None"
    result = utils_functions.generate_native_viewable_and_light_viewable(
        geode_object, data, folder_absolute_path
    )
    assert type(result) is dict
    assert type(result["name"]) is str
    assert type(result["native_file_name"]) is str
    assert re.match(r"native\.[a-zA-Z0-9]+", result["native_file_name"])
    assert type(result["viewable_file_name"]) is str
    assert re.match(r"viewable\.[a-zA-Z0-9]+", result["viewable_file_name"])
    assert type(result["id"]) is str
    assert re.match(r"[0-9a-f]{32}", result["id"])
    assert type(result["object_type"]) is str
    assert type(result["binary_light_viewable"]) is str

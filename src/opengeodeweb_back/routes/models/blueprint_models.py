import json
import os
import xml.etree.ElementTree as ET
import flask

from src.opengeodeweb_back import geode_functions, utils_functions

routes = flask.Blueprint("models", __name__)


@routes.before_request
def before_request():
    if "ping" not in flask.request.path:
        utils_functions.increment_request_counter(flask.current_app)


@routes.teardown_request
def teardown_request(exception):
    if "ping" not in flask.request.path:
        utils_functions.decrement_request_counter(flask.current_app)
        utils_functions.update_last_request_time(flask.current_app)


schemas = os.path.join(os.path.dirname(__file__), "schemas")

with open(os.path.join(schemas, "components.json"), "r") as file:
    components_json = json.load(file)


@routes.route(components_json["route"], methods=components_json["methods"])
def print_vtm_file():
    utils_functions.validate_request(flask.request, components_json)
    vtm_file_path = os.path.join(
        flask.current_app.config["DATA_FOLDER_PATH"], flask.request.json["id"] + ".vtm"
    )

    tree = ET.parse(vtm_file_path)
    root = tree.getroot()
    uuid_to_flat_index = {}
    current_index = 1

    for elem in root.iter():
        if "uuid" in elem.attrib and elem.tag == "DataSet":
            uuid_to_flat_index[elem.attrib["uuid"]] = current_index
            current_index += 1

    print(f"{uuid_to_flat_index=}", flush=True)

    return flask.make_response(
        {"uuid_to_flat_index": uuid_to_flat_index},
        200,
    )

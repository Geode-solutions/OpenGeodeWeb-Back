import json
import os
import xml.etree.ElementTree as ET
import flask
from ... import geode_functions, utils_functions

routes = flask.Blueprint("models", __name__, url_prefix="/models")


schemas = os.path.join(os.path.dirname(__file__), "schemas")

with open(os.path.join(schemas, "vtm_component_indices.json"), "r") as file:
    vtm_component_indices_json = json.load(file)


@routes.route(
    vtm_component_indices_json["route"], methods=vtm_component_indices_json["methods"]
)
def uuid_to_flat_index():

    print(f"uuid_to_flat_index : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, vtm_component_indices_json)
    vtm_file_path = os.path.join(
        flask.current_app.config["DATA_FOLDER_PATH"], flask.request.json["id"] + ".vtm"
    )

    tree = ET.parse(vtm_file_path)
    root = tree.find("vtkMultiBlockDataSet")
    uuid_to_flat_index = {}
    current_index = 0

    for elem in root.iter():
        if "uuid" in elem.attrib and elem.tag == "DataSet":
            uuid_to_flat_index[elem.attrib["uuid"]] = current_index

        current_index += 1

    return flask.make_response(
        {"uuid_to_flat_index": uuid_to_flat_index},
        200,
    )


def extract_model_uuids(geode_object, file_path):
    model = geode_functions.load(geode_object, file_path)
    mesh_components = model.mesh_components()

    uuid_dict = {}

    for mesh_component, ids in mesh_components.items():
        component_name = mesh_component.get()
        uuid_dict[component_name] = [id.string() for id in ids]

    return uuid_dict


with open(os.path.join(schemas, "mesh_components.json"), "r") as file:
    mesh_components_json = json.load(file)


@routes.route(mesh_components_json["route"], methods=mesh_components_json["methods"])
def extract_uuids_endpoint():
    print(f"extract_uuids_endpoint : {flask.request=}", flush=True)

    utils_functions.validate_request(flask.request, mesh_components_json)

    file_path = os.path.join(
        flask.current_app.config["DATA_FOLDER_PATH"], flask.request.json["filename"]
    )

    if not os.path.exists(file_path):
        return flask.make_response({"error": "File not found"}, 404)

    uuid_dict = extract_model_uuids(flask.request.json["geode_object"], file_path)
    return flask.make_response({"uuid_dict": uuid_dict}, 200)

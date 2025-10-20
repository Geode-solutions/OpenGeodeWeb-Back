import json
import os
import xml.etree.ElementTree as ET
import flask

from opengeodeweb_back import geode_functions, utils_functions
from . import schemas

routes = flask.Blueprint("models", __name__, url_prefix="/models")
schemas_folder = os.path.join(os.path.dirname(__file__), "schemas")

with open(os.path.join(schemas_folder, "vtm_component_indices.json"), "r") as file:
    vtm_component_indices_json: utils_functions.SchemaDict = json.load(file)


@routes.route(
    vtm_component_indices_json["route"], methods=vtm_component_indices_json["methods"]
)
def uuid_to_flat_index() -> flask.Response:
    utils_functions.validate_request(flask.request, vtm_component_indices_json)
    params = schemas.VtmComponentIndices(**flask.request.get_json())
    vtm_file_path = geode_functions.data_file_path(params.id, "viewable.vtm")
    tree = ET.parse(vtm_file_path)
    root = tree.find("vtkMultiBlockDataSet")
    if not root:
        raise Exception("Failed to read viewable file")
    uuid_to_flat_index = {}
    current_index = 0
    for elem in root.iter():
        if "uuid" in elem.attrib and elem.tag == "DataSet":
            uuid_to_flat_index[elem.attrib["uuid"]] = current_index
        current_index += 1
    return flask.make_response({"uuid_to_flat_index": uuid_to_flat_index}, 200)


with open(os.path.join(schemas_folder, "mesh_components.json"), "r") as file:
    mesh_components_json: utils_functions.SchemaDict = json.load(file)


@routes.route(mesh_components_json["route"], methods=mesh_components_json["methods"])
def extract_uuids_endpoint() -> flask.Response:
    utils_functions.validate_request(flask.request, mesh_components_json)
    params = schemas.MeshComponents(**flask.request.get_json())
    model = geode_functions.load_data(params.id)
    mesh_components = model.mesh_components()
    uuid_dict = {}
    for mesh_component, ids in mesh_components.items():
        component_name = mesh_component.get()
        uuid_dict[component_name] = [id.string() for id in ids]
    return flask.make_response({"uuid_dict": uuid_dict}, 200)

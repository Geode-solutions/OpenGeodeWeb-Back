import os
import xml.etree.ElementTree as ET
import flask
from opengeodeweb_microservice.schemas import get_schemas_dict

from opengeodeweb_back import geode_functions, utils_functions
from . import schemas

routes = flask.Blueprint("models", __name__, url_prefix="/models")
schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))


@routes.route(
    schemas_dict["vtm_component_indices"]["route"],
    methods=schemas_dict["vtm_component_indices"]["methods"],
)
def uuid_to_flat_index() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["vtm_component_indices"]
    )
    params = schemas.VtmComponentIndices.from_dict(flask.request.get_json())
    vtm_file_path = geode_functions.data_file_path(params.id, "viewable.vtm")
    tree = ET.parse(vtm_file_path)
    root = tree.find("vtkMultiBlockDataSet")
    if root is None:
        raise Exception("Failed to read viewable file")
    uuid_to_flat_index = {}
    current_index = 0
    for elem in root.iter():
        if "uuid" in elem.attrib and elem.tag == "DataSet":
            uuid_to_flat_index[elem.attrib["uuid"]] = current_index
        current_index += 1
    return flask.make_response({"uuid_to_flat_index": uuid_to_flat_index}, 200)


@routes.route(
    schemas_dict["mesh_components"]["route"],
    methods=schemas_dict["mesh_components"]["methods"],
)
def extract_uuids_endpoint() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["mesh_components"])
    params = schemas.MeshComponents.from_dict(flask.request.get_json())
    model = geode_functions.load_data(params.id)
    mesh_components = model.mesh_components()
    uuid_dict = {}
    for mesh_component, ids in mesh_components.items():
        component_name = mesh_component.get()
        uuid_dict[component_name] = [id.string() for id in ids]
    return flask.make_response({"uuid_dict": uuid_dict}, 200)

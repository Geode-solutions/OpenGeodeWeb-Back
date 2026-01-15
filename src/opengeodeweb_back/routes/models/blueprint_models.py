import os
import xml.etree.ElementTree as ET
import flask
from opengeodeweb_microservice.schemas import get_schemas_dict

from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.geode_objects.geode_model import GeodeModel
from . import schemas

routes = flask.Blueprint("models", __name__, url_prefix="/models")
schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))


@routes.route(
    schemas_dict["mesh_components"]["route"],
    methods=schemas_dict["mesh_components"]["methods"],
)
def mesh_components() -> flask.Response:
    json_data = utils_functions.validate_request(
        flask.request, schemas_dict["mesh_components"]
    )
    params = schemas.MeshComponents.from_dict(json_data)
    model = geode_functions.load_geode_object(params.id)
    if not isinstance(model, GeodeModel):
        flask.abort(400, f"{params.id} is not a GeodeModel")

    vtm_file_path = geode_functions.data_file_path(params.id, "viewable.vtm")
    tree = ET.parse(vtm_file_path)
    root = tree.find("vtkMultiBlockDataSet")
    if root is None:
        flask.abort(500, "Failed to read viewable file")
    uuid_to_flat_index = {}
    current_index = 0
    assert root is not None
    for elem in root.iter():
        if "uuid" in elem.attrib and elem.tag == "DataSet":
            uuid_to_flat_index[elem.attrib["uuid"]] = current_index
        current_index += 1
    model_mesh_components = model.mesh_components()
    mesh_components = []
    for mesh_component, ids in model_mesh_components.items():
        component_type = mesh_component.get()
        for id in ids:
            geode_id = id.string()
            component_name = geode_id
            viewer_id = uuid_to_flat_index[geode_id]

            mesh_component_object = {
                "id": params.id,
                "viewer_id": viewer_id,
                "geode_id": geode_id,
                "name": component_name,
                "type": component_type,
            }
            mesh_components.append(mesh_component_object)

    return flask.make_response({"mesh_components": mesh_components}, 200)

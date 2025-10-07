# Standard library imports
import json
import os
import uuid

# Third party imports
import flask
import opengeode
import werkzeug

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_back.utils_functions import save_all_viewables_and_return_info

routes = flask.Blueprint("create", __name__, url_prefix="/opengeodeweb_back/create")

schemas = os.path.join(os.path.dirname(__file__), "schemas")

# Load schema for point creation
with open(os.path.join(schemas, "create_point.json"), "r") as file:
    create_point_json = json.load(file)

@routes.route(
    create_point_json["route"],
    methods=create_point_json["methods"]
)
def create_point():
    """Endpoint to create a single point in 3D space."""
    print(f"create_point : {flask.request=}", flush=True)

    utils_functions.validate_request(flask.request, create_point_json)

    # Extract data from request
    title = flask.request.json["title"]
    x = flask.request.json["x"]
    y = flask.request.json["y"]
    z = flask.request.json["z"]

    # Create the point set
    class_ = geode_functions.geode_object_class("PointSet3D")
    point_set = class_.create()
    builder = geode_functions.create_builder("PointSet3D", point_set)
    builder.create_point(opengeode.Point3D([x, y, z]))
    builder.set_name(title)

    # Save and get info
    result = save_all_viewables_and_return_info(
        geode_object="PointSet3D",
        data=point_set,
        input_file=None,
        additional_files=[]
    )

    # Prepare response with the title
    response = {
        "viewable_file_name": result["viewable_file_name"],
        "id": result["id"],
        "name": title,
        "native_file_name": result["native_file_name"],
        "object_type": result["object_type"],
        "geode_object": result["geode_object"],
    }
    
    # Add binary_light_viewable if it exists
    if "binary_light_viewable" in result:
        response["binary_light_viewable"] = result["binary_light_viewable"]

    return flask.make_response(response, 200)


# Load schema for AOI creation
with open(os.path.join(schemas, "create_aoi.json"), "r") as file:
    create_aoi_json = json.load(file)

@routes.route(
    create_aoi_json["route"],
    methods=create_aoi_json["methods"]
)
def create_aoi():
    """Endpoint to create an Area of Interest (AOI) as an EdgedCurve3D."""
    print(f"create_aoi : {flask.request=}", flush=True)

    utils_functions.validate_request(flask.request, create_aoi_json)

    # Extract data from request
    name = flask.request.json["name"]
    points = flask.request.json["points"]
    z = flask.request.json["z"]

    # Create the edged curve
    class_ = geode_functions.geode_object_class("EdgedCurve3D")
    edged_curve = class_.create()
    builder = geode_functions.create_builder("EdgedCurve3D", edged_curve)
    builder.set_name(name)

    # Create vertices first
    vertex_indices = []
    for point in points:
        vertex_id = builder.create_point(opengeode.Point3D([point["x"], point["y"], z]))
        vertex_indices.append(vertex_id)

    # Create edges between consecutive vertices and close the loop
    num_vertices = len(vertex_indices)
    for i in range(num_vertices):
        edge_id = builder.create_edge()
        next_i = (i + 1) % num_vertices  # Wrap around to close the loop
        builder.set_edge_vertex(
            opengeode.EdgeVertex(edge_id, 0), vertex_indices[i]
        )
        builder.set_edge_vertex(
            opengeode.EdgeVertex(edge_id, 1), vertex_indices[next_i]
        )

    # Save and get info
    result = save_all_viewables_and_return_info(
        geode_object="EdgedCurve3D",
        data=edged_curve,
        input_file=None,
        additional_files=[]
    )

    # Prepare response
    response = {
        "viewable_file_name": result["viewable_file_name"],
        "id": result["id"],
        "name": name,
        "native_file_name": result["native_file_name"],
        "object_type": result["object_type"],
        "geode_object": result["geode_object"],
    }
    
    # Add binary_light_viewable if it exists
    if "binary_light_viewable" in result:
        response["binary_light_viewable"] = result["binary_light_viewable"]

    return flask.make_response(response, 200)

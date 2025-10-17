# Standard library imports
import json
import os
from typing import Any, TypedDict

# Third party imports
import flask
import opengeode

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions

routes = flask.Blueprint("create", __name__, url_prefix="/create")
schemas = os.path.join(os.path.dirname(__file__), "schemas")

# --- Type definitions ---
type SchemaDict = dict[str, Any]


class PointDict(TypedDict):
    x: float
    y: float


class CreatePointParams(TypedDict):
    name: str
    x: float
    y: float
    z: float


class CreateAOIParams(TypedDict):
    name: str
    points: list[PointDict]
    z: float


# Load schemas
with open(os.path.join(schemas, "create_point.json"), "r") as file:
    create_point_json: SchemaDict = json.load(file)


@routes.route(create_point_json["route"], methods=create_point_json["methods"])
def create_point() -> flask.Response:
    """Endpoint to create a single point in 3D space."""
    print(f"create_point : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, create_point_json)

    # Extract and validate data from request
    params: CreatePointParams = flask.request.get_json()
    name = params["name"]
    x = params["x"]
    y = params["y"]
    z = params["z"]

    # Create the point
    class_ = geode_functions.geode_object_class("PointSet3D")
    pointset = class_.create()
    builder = geode_functions.create_builder("PointSet3D", pointset)
    builder.set_name(name)
    builder.create_point(opengeode.Point3D([x, y, z]))

    # Save and get info
    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        geode_object="PointSet3D",
        data=pointset,
    )
    result["name"] = name
    return flask.make_response(result, 200)


# Load schema for AOI creation
with open(os.path.join(schemas, "create_aoi.json"), "r") as file:
    create_aoi_json: SchemaDict = json.load(file)


@routes.route(create_aoi_json["route"], methods=create_aoi_json["methods"])
def create_aoi() -> flask.Response:
    """Endpoint to create an Area of Interest (AOI) as an EdgedCurve3D."""
    print(f"create_aoi : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, create_aoi_json)

    # Extract and validate data from request
    params: CreateAOIParams = flask.request.get_json()
    name = params["name"]
    points = params["points"]
    z = params["z"]

    # Create the edged curve
    class_ = geode_functions.geode_object_class("EdgedCurve3D")
    edged_curve = class_.create()
    builder = geode_functions.create_builder("EdgedCurve3D", edged_curve)
    builder.set_name(name)

    # Create vertices first
    vertex_indices: list[int] = []
    for point in points:
        vertex_id = builder.create_point(opengeode.Point3D([point["x"], point["y"], z]))
        vertex_indices.append(vertex_id)

    # Create edges between consecutive vertices and close the loop
    num_vertices = len(vertex_indices)
    for i in range(num_vertices):
        next_i = (i + 1) % num_vertices
        edge_id = builder.create_edge()
        builder.set_edge_vertex(opengeode.EdgeVertex(edge_id, 0), vertex_indices[i])
        builder.set_edge_vertex(
            opengeode.EdgeVertex(edge_id, 1), vertex_indices[next_i]
        )

    # Save and get info
    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        geode_object="EdgedCurve3D",
        data=edged_curve,
    )
    result["name"] = name
    return flask.make_response(result, 200)

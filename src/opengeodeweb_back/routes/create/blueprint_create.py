# Standard library imports
import json
import os
from typing import cast, Any
# Third party imports
import flask
import opengeode
# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.utils_functions import save_all_viewables_and_return_info

routes = flask.Blueprint("create", __name__, url_prefix="/opengeodeweb_back/create")
schemas = os.path.join(os.path.dirname(__file__), "schemas")

# --- Type definitions for JSON and RPC ---
type JsonPrimitive = str | int | float | bool
type JsonValue = JsonPrimitive | dict[str, JsonValue] | list[JsonValue]
type RpcParams = dict[str, JsonValue]
type SchemaDict = dict[str, Any]  # Changé pour éviter cast sur json.load

# --- Specialized type aliases for each RPC endpoint ---
type PointDict = dict[str, float]  # {"x": float, "y": float}
type CreatePointParams = dict[str, str | float]  # {"name": str, "x": float, "y": float, "z": float}
type CreateAOIParams = dict[str, str | float | list[PointDict]]  # {"name": str, "points": list[PointDict], "z": float}

# Load schema for point creation
with open(os.path.join(schemas, "create_point.json"), "r") as file:
    create_point_json: SchemaDict = json.load(file)

@routes.route(
    create_point_json["route"],
    methods=create_point_json["methods"]
)
def create_point() -> flask.Response:
    """Endpoint to create a single point in 3D space."""
    print(f"create_point : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, create_point_json)

    # Extract and validate data from request
    params: CreatePointParams = flask.request.get_json()  # type: ignore
    name: str = params["name"]  # type: ignore
    x: float = params["x"]  # type: ignore
    y: float = params["y"]  # type: ignore
    z: float = params["z"]  # type: ignore

    # Create the point
    class_ = geode_functions.geode_object_class("PointSet3D")
    pointset = class_.create()
    builder = geode_functions.create_builder("PointSet3D", pointset)
    builder.set_name(name)
    builder.create_point(opengeode.Point3D([x, y, z]))

    # Save and get info
    result = save_all_viewables_and_return_info(
        geode_object="PointSet3D",
        data=pointset,
    )
    result["name"] = name
    if "binary_light_viewable" not in result:
        raise ValueError("binary_light_viewable is missing in the result")
    return flask.make_response(result, 200)

# Load schema for AOI creation
with open(os.path.join(schemas, "create_aoi.json"), "r") as file:
    create_aoi_json: SchemaDict = json.load(file)

@routes.route(
    create_aoi_json["route"],
    methods=create_aoi_json["methods"]
)
def create_aoi() -> flask.Response:
    """Endpoint to create an Area of Interest (AOI) as an EdgedCurve3D."""
    print(f"create_aoi : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, create_aoi_json)

    # Extract and validate data from request
    params: CreateAOIParams = flask.request.get_json()  # type: ignore
    name: str = params["name"]  # type: ignore
    points: list[PointDict] = params["points"]  # type: ignore
    z: float = params["z"]  # type: ignore

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
        builder.set_edge_vertex(opengeode.EdgeVertex(edge_id, 1), vertex_indices[next_i])

    # Save and get info
    result = save_all_viewables_and_return_info(
        geode_object="EdgedCurve3D",
        data=edged_curve,
    )
    result["name"] = name
    if "binary_light_viewable" not in result:
        raise ValueError("binary_light_viewable is missing in the result")
    return flask.make_response(result, 200)

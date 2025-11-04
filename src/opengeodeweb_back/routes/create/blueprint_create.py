# Standard library imports
import os

# Third party imports
import flask
import opengeode
from opengeodeweb_microservice.schemas import get_schemas_dict

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from . import schemas

routes = flask.Blueprint("create", __name__, url_prefix="/create")
schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))


@routes.route(
    schemas_dict["create_point"]["route"],
    methods=schemas_dict["create_point"]["methods"],
)
def create_point() -> flask.Response:
    """Endpoint to create a single point in 3D space."""
    print(f"create_point : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, schemas_dict["create_point"])
    params = schemas.CreatePoint.from_dict(flask.request.get_json())

    # Create the point
    pointset = geode_functions.geode_object_class("PointSet3D").create()
    builder = geode_functions.create_builder("PointSet3D", pointset)
    builder.set_name(params.name)
    builder.create_point(opengeode.Point3D([params.x, params.y, params.z]))

    # Save and get info
    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        geode_object="PointSet3D",
        data=pointset,
    )
    return flask.make_response(result, 200)


@routes.route(
    schemas_dict["create_aoi"]["route"], methods=schemas_dict["create_aoi"]["methods"]
)
def create_aoi() -> flask.Response:
    """Endpoint to create an Area of Interest (AOI) as an EdgedCurve3D."""
    print(f"create_aoi : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, schemas_dict["create_aoi"])
    params = schemas.CreateAoi.from_dict(flask.request.get_json())

    # Create the edged curve
    edged_curve = geode_functions.geode_object_class("EdgedCurve3D").create()
    builder = geode_functions.create_builder("EdgedCurve3D", edged_curve)
    builder.set_name(params.name)

    # Create vertices first
    for point in params.points:
        # pp = opengeode.Point3D([point.x, point.y, params.z])
        builder.create_point(opengeode.Point3D([point.x, point.y, params.z]))

    # Create edges between consecutive vertices and close the loop
    num_vertices = len(params.points)
    for i in range(num_vertices):
        next_i = (i + 1) % num_vertices
        builder.create_edge_with_vertices(i, next_i)

    # Save and get info
    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        geode_object="EdgedCurve3D",
        data=edged_curve,
    )
    return flask.make_response(result, 200)


@routes.route(
    schemas_dict["create_voi"]["route"], methods=schemas_dict["create_voi"]["methods"]
)
def create_voi() -> flask.Response:
    """Endpoint to create a Volume of Interest (VOI) as an EdgedCurve3D (a bounding box)."""
    print(f"create_voi : {flask.request=}", flush=True)
    utils_functions.validate_request(flask.request, schemas_dict["create_voi"])
    params = schemas.CreateVoi.from_dict(flask.request.get_json())

    aoi_data = geode_functions.get_data_info(params.aoi_id)
    if not aoi_data:
        flask.abort(404, f"AOI with id {params.aoi_id} not found")

    edged_curve_aoi = geode_functions.load_data(params.aoi_id)
    if not isinstance(edged_curve_aoi, opengeode.EdgedCurve3D):
        flask.abort(400, "Referenced object is not an EdgedCurve3D (AOI)")

    bbox_aoi = edged_curve_aoi.bounding_box()
    min_x = bbox_aoi.min().value(0)
    min_y = bbox_aoi.min().value(1)
    max_x = bbox_aoi.max().value(0)
    max_y = bbox_aoi.max().value(1)

    aoi_vertices = [
        (min_x, min_y),
        (max_x, min_y),
        (max_x, max_y),
        (min_x, max_y),
    ]

    edged_curve = geode_functions.geode_object_class("EdgedCurve3D").create()
    builder = geode_functions.create_builder("EdgedCurve3D", edged_curve)
    builder.set_name(params.name)

    z_min = params.z_min
    z_max = params.z_max


    for x, y in aoi_vertices:
        builder.create_point(opengeode.Point3D([x, y, z_min]))

    for x, y in aoi_vertices:
        builder.create_point(opengeode.Point3D([x, y, z_max]))


    bottom_edges = [(i, (i + 1) % 4) for i in range(4)]

    top_edges = [(i + 4, (i + 1) % 4 + 4) for i in range(4)]

    vertical_edges = [(i, i + 4) for i in range(4)]

    all_edges = bottom_edges + top_edges + vertical_edges

    for v1, v2 in all_edges:
        builder.create_edge_with_vertices(v1, v2)

    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        geode_object="EdgedCurve3D",
        data=edged_curve,
    )
    result["aoi_id"] = params.aoi_id  
    return flask.make_response(result, 200)
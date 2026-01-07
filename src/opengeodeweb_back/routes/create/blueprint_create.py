# Standard library imports
import os

# Third party imports
import flask
import opengeode
from opengeodeweb_microservice.schemas import get_schemas_dict

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
import opengeodeweb_back.routes.create.schemas as schemas
from opengeodeweb_back.geode_objects.geode_point_set3d import GeodePointSet3D
from opengeodeweb_back.geode_objects.geode_edged_curve3d import GeodeEdgedCurve3D

routes = flask.Blueprint("create", __name__, url_prefix="/create")
schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))


@routes.route(
    schemas_dict["point"]["route"],
    methods=schemas_dict["point"]["methods"],
)
def point() -> flask.Response:
    """Endpoint to create a single point in 3D space."""
    json_data = utils_functions.validate_request(flask.request, schemas_dict["point"])
    params = schemas.Point.from_dict(json_data)

    # Create the point
    pointset = GeodePointSet3D()
    builder = pointset.builder()
    builder.set_name(params.name)
    builder.create_point(opengeode.Point3D([params.x, params.y, params.z]))

    # Save and get info
    result = utils_functions.generate_native_viewable_and_light_viewable_from_object(
        pointset
    )
    return flask.make_response(result, 200)

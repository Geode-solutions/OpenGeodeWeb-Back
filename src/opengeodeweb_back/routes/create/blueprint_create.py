# Standard library imports

# Third party imports
import flask
import opengeode

# Local application imports
from opengeodeweb_back import utils_functions
from opengeodeweb_back.geode_objects.geode_edged_curve3d import GeodeEdgedCurve3D
from opengeodeweb_back.geode_objects.geode_point_set3d import GeodePointSet3D
from opengeodeweb_back.geode_objects.geode_polygonal_surface3d import (
    GeodePolygonalSurface3D,
)
from opengeodeweb_back.routes.create import schemas
from opengeodeweb_back.typed_route import typed_route

routes = flask.Blueprint("create", __name__, url_prefix="/create")


@typed_route(routes, schemas.point_set_route)
def point_set(params: schemas.PointSet) -> schemas.PointSetResponse:

    pointset = GeodePointSet3D()
    builder = pointset.builder()
    builder.set_name(params.name)
    for point in params.points:
        builder.create_point(opengeode.Point3D([point.x, point.y, point.z]))

    return schemas.PointSetResponse.from_dict(
        utils_functions.generate_files_from_object(pointset)
    )


@typed_route(routes, schemas.edged_curve_route)
def edged_curve(params: schemas.EdgedCurve) -> schemas.EdgedCurveResponse:
    """Endpoint to create an edged curve in 3D space."""
    edged_curve_obj = GeodeEdgedCurve3D()
    builder = edged_curve_obj.builder()
    builder.set_name(params.name)
    for point in params.points:
        builder.create_point(opengeode.Point3D([point.x, point.y, point.z]))

    for edge in params.edges:
        builder.create_edge_with_vertices(edge[0], edge[1])

    return schemas.EdgedCurveResponse.from_dict(
        utils_functions.generate_files_from_object(edged_curve_obj)
    )


@typed_route(routes, schemas.polygonal_surface_route)
def polygonal_surface(
    params: schemas.PolygonalSurface,
) -> schemas.PolygonalSurfaceResponse:
    """Endpoint to create a polygonal surface in 3D space."""
    polygonal_surface_obj = GeodePolygonalSurface3D()
    builder = polygonal_surface_obj.builder()
    builder.set_name(params.name)
    for point in params.points:
        builder.create_point(opengeode.Point3D([point.x, point.y, point.z]))

    for polygon in params.polygons:
        builder.create_polygon(polygon)

    builder.compute_polygon_adjacencies()

    return schemas.PolygonalSurfaceResponse.from_dict(
        utils_functions.generate_files_from_object(polygonal_surface_obj)
    )

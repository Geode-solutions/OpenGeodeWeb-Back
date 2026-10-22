# Standard library imports

# Third party imports
import flask
import opengeode_geosciences as og_geosciences

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep
from opengeodeweb_back.geode_objects.geode_edged_curve2d import GeodeEdgedCurve2D
from opengeodeweb_back.geode_objects.geode_edged_curve3d import GeodeEdgedCurve3D
from opengeodeweb_back.geode_objects.geode_point_set2d import GeodePointSet2D
from opengeodeweb_back.geode_objects.geode_point_set3d import GeodePointSet3D
from opengeodeweb_back.geode_objects.geode_section import GeodeSection
from opengeodeweb_back.geode_objects.geode_solid_mesh3d import GeodeSolidMesh3D
from opengeodeweb_back.geode_objects.geode_surface_mesh2d import GeodeSurfaceMesh2D
from opengeodeweb_back.geode_objects.geode_surface_mesh3d import GeodeSurfaceMesh3D
from opengeodeweb_back.routes.crs import schemas
from opengeodeweb_back.typed_route import typed_route

routes = flask.Blueprint("crs", __name__, url_prefix="/crs")

CRS_GEODE_OBJECTS = (
    GeodeBRep,
    GeodeSection,
    GeodePointSet2D,
    GeodePointSet3D,
    GeodeEdgedCurve2D,
    GeodeEdgedCurve3D,
    GeodeSurfaceMesh2D,
    GeodeSurfaceMesh3D,
    GeodeSolidMesh3D,
)


@typed_route(routes, schemas.geographic_list_route)
def geographic_list(params: schemas.GeographicList) -> schemas.GeographicListResponse:
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type)
    infos = (
        og_geosciences.GeographicCoordinateSystem3D.geographic_coordinate_systems()
        if geode_object.is_3d()
        else og_geosciences.GeographicCoordinateSystem2D.geographic_coordinate_systems()
    )
    crs_list = [
        schemas.geographic_list.CRSList(name=info.name, code=info.code, authority=info.authority)
        for info in infos
    ]
    return schemas.GeographicListResponse(crs_list=crs_list)


@typed_route(routes, schemas.active_route)
def active(params: schemas.Active) -> schemas.ActiveResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    crs_manager = geode_object.crs_manager()
    crs = crs_manager.active_coordinate_reference_system()
    crs_info = None
    if isinstance(
        crs,
        og_geosciences.GeographicCoordinateSystem2D | og_geosciences.GeographicCoordinateSystem3D,
    ):
        info = crs.info()
        crs_info = schemas.active.CRSInfo(authority=info.authority, code=info.code, name=info.name)
    return schemas.ActiveResponse(
        crs_name=crs_manager.active_coordinate_reference_system_name(),
        crs_info=crs_info,
    )


@typed_route(routes, schemas.assign_geographic_route)
def assign_geographic(params: schemas.AssignGeographic) -> schemas.AssignGeographicResponse:
    data = geode_functions.get_data_info(params.id)
    geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
        geode_functions.data_file_path(params.id, data.native_file)
    )
    if not isinstance(geode_object, CRS_GEODE_OBJECTS):
        flask.abort(400, f"{params.id} does not support coordinate reference systems")
    info = og_geosciences.GeographicCoordinateSystemInfo(params.authority, params.code, params.name)
    geode_object.assign_crs(info.authority_code(), info)
    utils_functions.save_all_viewables_and_return_info(
        geode_object, data, geode_functions.data_file_path(params.id)
    )
    return schemas.AssignGeographicResponse()

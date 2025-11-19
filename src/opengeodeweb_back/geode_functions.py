# Standard library imports
import os

# Third party imports
import opengeode_geosciences as og_gs
import opengeode as og
import werkzeug
import flask
from typing import Any

# Local application imports
from .geode_objects import geode_objects, geode_meshes, geode_models
from .geode_objects.types import (
    GeodeObjectType,
    geode_object_type,
    GeodeMeshType,
    geode_mesh_type,
    GeodeModelType,
    geode_model_type,
)
from .geode_objects.geode_object import GeodeObject
from .geode_objects.geode_mesh import GeodeMesh
from .geode_objects.geode_model import GeodeModel
from . import utils_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session


def data_file_path(data_id: str, filename: str | None = None) -> str:
    data_folder_path = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(data_folder_path, data_id)
    if filename is not None:
        return os.path.join(data_path, filename)
    return data_path


def geode_object_from_string(value: str) -> type[GeodeObject]:
    return geode_objects[geode_object_type(value)]


def geode_mesh_from_string(value: str) -> type[GeodeMesh]:
    return geode_meshes[geode_mesh_type(value)]


def geode_model_from_string(value: str) -> type[GeodeModel]:
    return geode_models[geode_model_type(value)]


def load_object_data(data_id: str) -> GeodeObject:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data.native_file_name)
    print("Loading file: ", file_absolute_path)
    print("File exists: ", os.path.exists(file_absolute_path))
    return geode_object_from_string(data.geode_object).load(file_absolute_path)


def load_mesh_data(data_id: str) -> GeodeMesh:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data.native_file_name)
    print("Loading file: ", file_absolute_path)
    print("File exists: ", os.path.exists(file_absolute_path))
    return geode_mesh_from_string(data.geode_object).load_mesh(file_absolute_path)


def load_model_data(data_id: str) -> GeodeModel:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data.native_file_name)
    print("Loading file: ", file_absolute_path)
    print("File exists: ", os.path.exists(file_absolute_path))
    return geode_model_from_string(data.geode_object).load_model(file_absolute_path)


def get_data_info(data_id: str) -> Data:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")
    return data


def upload_file_path(filename: str) -> str:
    upload_folder = flask.current_app.config["UPLOAD_FOLDER"]
    secure_filename = werkzeug.utils.secure_filename(filename)
    return os.path.abspath(os.path.join(upload_folder, secure_filename))


def geode_object_output_extensions(
    geode_object: GeodeObject,
) -> dict[GeodeObjectType, dict[str, bool]]:
    results: dict[GeodeObjectType, dict[str, bool]] = {}
    for mixin_geode_object in geode_objects[geode_object.geode_object_type()].__mro__:
        output_extensions_method = getattr(
            mixin_geode_object, "output_extensions", None
        )
        if output_extensions_method is None:
            continue
        output_extensions = output_extensions_method.__func__(mixin_geode_object)
        if output_extensions is None:
            continue
        object_output_extensions: dict[str, bool] = {}
        is_saveable_method = getattr(mixin_geode_object, "is_saveable")
        for output_extension in output_extensions:
            bool_is_saveable = is_saveable_method(
                geode_object, f"test.{output_extension}"
            )
            object_output_extensions[output_extension] = bool_is_saveable
        if hasattr(mixin_geode_object, "geode_object_type"):
            results[mixin_geode_object.geode_object_type()] = object_output_extensions
    return results


# def assign_crs(geode_object_type: GeodeObjectType, data, crs_name: str, info):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_object_type].["crs"]["assign"](data, builder, crs_name, info)


# def convert_crs(geode_object_type: GeodeObjectType, data, crs_name: str, info):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_object_type].["crs"]["convert"](data, builder, crs_name, info)


# def create_crs(
#     geode_object_type: GeodeObjectType,
#     data,
#     name: str,
#     input_coordiante_system,
#     output_coordiante_system,
# ):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_object_type].["crs"]["create"](
#         data, builder, name, input_coordiante_system, output_coordiante_system
#     )


# def geographic_coordinate_systems_info(geode_object_type: GeodeObjectType, crs):
#     if is_3D(geode_object):
#         return og_gs.GeographicCoordinateSystemInfo3D(
#             crs["authority"], crs["code"], crs["name"]
#         )
#     else:
#         return og_gs.GeographicCoordinateSystemInfo2D(
#             crs["authority"], crs["code"], crs["name"]
#         )


# def coordinate_system(geode_object_type: GeodeObjectType, coordinate_system):
#     return og.CoordinateSystem2D(
#         [
#             og.Vector2D(
#                 og.Point2D(
#                     [coordinate_system["origin_x"], coordinate_system["origin_y"]]
#                 ),
#                 og.Point2D(
#                     [coordinate_system["point_1_x"], coordinate_system["point_1_y"]]
#                 ),
#             ),
#             og.Vector2D(
#                 og.Point2D(
#                     [coordinate_system["origin_x"], coordinate_system["origin_y"]]
#                 ),
#                 og.Point2D(
#                     [coordinate_system["point_2_x"], coordinate_system["point_2_y"]]
#                 ),
#             ),
#         ],
#         og.Point2D([coordinate_system["origin_x"], coordinate_system["origin_y"]]),
#     )


# def assign_geographic_coordinate_system_info(geode_object_type: GeodeObjectType, data, input_crs):
#     info = geographic_coordinate_systems_info(geode_object, input_crs)
#     assign_crs(geode_object, data, input_crs["name"], info)


# def convert_geographic_coordinate_system_info(geode_object_type: GeodeObjectType, data, output_crs):
#     info = geographic_coordinate_systems_info(geode_object, output_crs)
#     convert_crs(geode_object, data, output_crs["name"], info)


# def create_coordinate_system(
#     geode_object_type: GeodeObjectType, data, name, input_coordinate_points, output_coordinate_points
# ):
#     input_coordiante_system = coordinate_system(geode_object, input_coordinate_points)
#     output_coordiante_system = coordinate_system(geode_object, output_coordinate_points)
#     create_crs(
#         geode_object, data, name, input_coordiante_system, output_coordiante_system
#     )

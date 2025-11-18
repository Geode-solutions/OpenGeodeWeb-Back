# Standard library imports
import os

# Third party imports
import opengeode_geosciences as og_gs
import opengeode as og
import werkzeug
import flask
from typing import Any

# Local application imports
from .geode_objects import geode_objects
from .geode_objects.geode_object import GeodeType, GeodeObject, to_geode_type
from . import utils_functions
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session


def data_file_path(data_id: str, filename: str | None) -> str:
    data_folder_path = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(data_folder_path, data_id)
    if filename is not None:
        return os.path.join(data_path, filename)
    return data_path


def load_data(data_id: str) -> GeodeObject:
    data_entry = Data.get(data_id)
    if not data_entry:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data_entry.native_file_name)
    print("Loading file: ", file_absolute_path)
    print("File exists: ", os.path.exists(file_absolute_path))
    return geode_objects[to_geode_type(data_entry.geode_object)].load(
        file_absolute_path
    )


def get_data_info(data_id: str) -> Data:
    data_entry = Data.get(data_id)
    if not data_entry:
        flask.abort(404, f"Data with id {data_id} not found")
    return data_entry


def upload_file_path(filename: str) -> str:
    upload_folder = flask.current_app.config["UPLOAD_FOLDER"]
    secure_filename = werkzeug.utils.secure_filename(filename)
    return os.path.abspath(os.path.join(upload_folder, secure_filename))


def geode_object_output_extensions(
    geode_object: GeodeObject,
) -> dict[GeodeType, dict[str, bool]]:
    results: dict[GeodeType, dict[str, bool]] = {}
    for mixin_geode_object in geode_objects[geode_object.geode_type()].__mro__:
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
        if hasattr(mixin_geode_object, "geode_type"):
            results[mixin_geode_object.geode_type()] = object_output_extensions
    return results


# def assign_crs(geode_type: GeodeType, data, crs_name: str, info):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_type].["crs"]["assign"](data, builder, crs_name, info)


# def convert_crs(geode_type: GeodeType, data, crs_name: str, info):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_type].["crs"]["convert"](data, builder, crs_name, info)


# def create_crs(
#     geode_type: GeodeType,
#     data,
#     name: str,
#     input_coordiante_system,
#     output_coordiante_system,
# ):
#     builder = create_builder(geode_object, data)
#     geode_objects[geode_type].["crs"]["create"](
#         data, builder, name, input_coordiante_system, output_coordiante_system
#     )


# def geographic_coordinate_systems_info(geode_type: GeodeType, crs):
#     if is_3D(geode_object):
#         return og_gs.GeographicCoordinateSystemInfo3D(
#             crs["authority"], crs["code"], crs["name"]
#         )
#     else:
#         return og_gs.GeographicCoordinateSystemInfo2D(
#             crs["authority"], crs["code"], crs["name"]
#         )


# def coordinate_system(geode_type: GeodeType, coordinate_system):
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


# def assign_geographic_coordinate_system_info(geode_type: GeodeType, data, input_crs):
#     info = geographic_coordinate_systems_info(geode_object, input_crs)
#     assign_crs(geode_object, data, input_crs["name"], info)


# def convert_geographic_coordinate_system_info(geode_type: GeodeType, data, output_crs):
#     info = geographic_coordinate_systems_info(geode_object, output_crs)
#     convert_crs(geode_object, data, output_crs["name"], info)


# def create_coordinate_system(
#     geode_type: GeodeType, data, name, input_coordinate_points, output_coordinate_points
# ):
#     input_coordiante_system = coordinate_system(geode_object, input_coordinate_points)
#     output_coordiante_system = coordinate_system(geode_object, output_coordinate_points)
#     create_crs(
#         geode_object, data, name, input_coordiante_system, output_coordiante_system
#     )

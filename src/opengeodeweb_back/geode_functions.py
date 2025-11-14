# Standard library imports
import os

# Third party imports
import opengeode_geosciences as og_gs
import opengeode as og 
import werkzeug
import flask
from typing import Any

# Local application imports
from .geode_objects import geode_objects,GeodeType, GeodeObject, to_geode_type
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
    return geode_objects[to_geode_type(data_entry.geode_object)].load(file_absolute_path)


def get_data_info(data_id: str) -> Data:
    data_entry = Data.get(data_id)
    if not data_entry:
        flask.abort(404, f"Data with id {data_id} not found")
    return data_entry


def upload_file_path(filename: str) -> str:
    upload_folder = flask.current_app.config["UPLOAD_FOLDER"]
    secure_filename = werkzeug.utils.secure_filename(filename)
    return os.path.abspath(os.path.join(upload_folder, secure_filename))


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


def filter_geode_objects(key: str | None = None)-> list[GeodeType]:
    filtered_geode_objects = []
    for geode_object, value in geode_objects.items():
        if key != None and key != "":
            if key in value:
                if type(value[key]) == bool:
                    filtered_geode_objects.append(geode_object)
                else:
                    filtered_geode_objects.append(geode_object)
        else:
            filtered_geode_objects.append(geode_object)
    filtered_geode_objects.sort()
    return filtered_geode_objects


def list_input_extensions(key: str | None = None) -> list[str]:
    extensions_list = []
    for geode_object in filter_geode_objects(key):
        extensions_list += geode_object_input_extensions(geode_object)
    extensions_list = list(set(extensions_list))
    extensions_list.sort()
    return extensions_list


def has_creator(geode_type: GeodeType, extension: str):
    return input_factory(geode_object).has_creator(extension)


def list_geode_objects(
    file_absolute_path: str,
    key: str | None = None,
):
    return_dict = {}
    file_extension = utils_functions.extension_from_filename(
        os.path.basename(file_absolute_path)
    )
    geode_objects_filtered_list = filter_geode_objects(key)
    for geode_object in geode_objects_filtered_list:
        if has_creator(geode_object, file_extension):
            loadability_score = is_loadable(geode_object, file_absolute_path)
            priority_score = object_priority(geode_object, file_absolute_path)
            return_dict[geode_object] = {
                "is_loadable": loadability_score,
                "object_priority": priority_score,
            }
    return return_dict


def geode_objects_output_extensions(geode_type: GeodeType, data):
    geode_objects_output_extensions_dict = {}
    output_extensions = geode_object_output_extensions(geode_object)
    extensions_dict = {}
    for output_extension in output_extensions:
        bool_is_saveable = is_saveable(geode_object, data, f"test.{output_extension}")
        extensions_dict[output_extension] = {"is_saveable": bool_is_saveable}
    geode_objects_output_extensions_dict[geode_object] = extensions_dict

    if "parent" in geode_objects[geode_type]..keys():
        parent_geode_object = geode_objects[geode_type].["parent"]
        geode_objects_output_extensions_dict.update(
            geode_objects_output_extensions(parent_geode_object, data)
        )
    return geode_objects_output_extensions_dict


def get_inspector_children(obj):
    new_object = {}

    if "inspection_type" in dir(obj):
        new_object["title"] = obj.inspection_type()
        new_object["nb_issues"] = 0
        new_object["children"] = []
        for child in dir(obj):
            if not child.startswith("__") and not child in [
                "inspection_type",
                "string",
            ]:
                child_instance = obj.__getattribute__(child)
                child_object = get_inspector_children(child_instance)
                new_object["children"].append(child_object)
                new_object["nb_issues"] += child_object["nb_issues"]
    else:
        new_object["title"] = obj.description()
        nb_issues = obj.nb_issues()
        new_object["nb_issues"] = nb_issues
        if nb_issues > 0:
            issues = obj.string().split("\n")
            new_object["issues"] = issues
    return new_object


def geographic_coordinate_systems(geode_type: GeodeType):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystem3D.geographic_coordinate_systems()
    else:
        return og_gs.GeographicCoordinateSystem2D.geographic_coordinate_systems()


def geographic_coordinate_systems_info(geode_type: GeodeType, crs):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystemInfo3D(
            crs["authority"], crs["code"], crs["name"]
        )
    else:
        return og_gs.GeographicCoordinateSystemInfo2D(
            crs["authority"], crs["code"], crs["name"]
        )


def coordinate_system(geode_type: GeodeType, coordinate_system):
    return og.CoordinateSystem2D(
        [
            og.Vector2D(
                og.Point2D(
                    [coordinate_system["origin_x"], coordinate_system["origin_y"]]
                ),
                og.Point2D(
                    [coordinate_system["point_1_x"], coordinate_system["point_1_y"]]
                ),
            ),
            og.Vector2D(
                og.Point2D(
                    [coordinate_system["origin_x"], coordinate_system["origin_y"]]
                ),
                og.Point2D(
                    [coordinate_system["point_2_x"], coordinate_system["point_2_y"]]
                ),
            ),
        ],
        og.Point2D([coordinate_system["origin_x"], coordinate_system["origin_y"]]),
    )


def assign_geographic_coordinate_system_info(geode_type: GeodeType, data, input_crs):
    info = geographic_coordinate_systems_info(geode_object, input_crs)
    assign_crs(geode_object, data, input_crs["name"], info)


def convert_geographic_coordinate_system_info(geode_type: GeodeType, data, output_crs):
    info = geographic_coordinate_systems_info(geode_object, output_crs)
    convert_crs(geode_object, data, output_crs["name"], info)


def create_coordinate_system(
    geode_type: GeodeType, data, name, input_coordinate_points, output_coordinate_points
):
    input_coordiante_system = coordinate_system(geode_object, input_coordinate_points)
    output_coordiante_system = coordinate_system(geode_object, output_coordinate_points)
    create_crs(
        geode_object, data, name, input_coordiante_system, output_coordiante_system
    )

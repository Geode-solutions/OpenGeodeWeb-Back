# Standard library imports
import base64
import os
import time
import threading
import uuid

# Third party imports
import flask
import opengeode_geosciences as og_gs
import opengeode as og
import pkg_resources
import werkzeug

# Local application imports
from .geode_objects import objects_list


def list_all_input_extensions(crs=False):
    """
    Purpose:
        Function that returns a list of all input extensions
    Args:
        crs -- Tells the function if we want the geode_objects that have a crs
    Returns:
        An ordered list of input file extensions
    """
    List = []
    geode_object_dict = objects_list()

    for geode_object in geode_object_dict.values():
        values = geode_object["input"]

        # if crs == True:
        #     if "crs" not in geode_object:
        #         continue
        for value in values:
            list_creators = value.list_creators()
            for creator in list_creators:
                if creator not in List:
                    List.append(creator)
    List.sort()
    return List


def list_objects(extension: str, is_viewable: bool = True):
    """
    Purpose:
        Function that returns a list of objects that can handle a file, given his extension
    Args:
        extension -- The extension of the file
    Returns:
        An ordered list of object's names
    """
    return_list = []
    geode_object_dict = objects_list()

    for object_, values in geode_object_dict.items():
        # if values["is_viewable"] == is_viewable:
        list_values = values["input"]
        for value in list_values:
            if value.has_creator(extension):
                if object_ not in return_list:
                    return_list.append(object_)
    return_list.sort()
    return return_list


def list_output_file_extensions(object: str):
    """
    Purpose:
        Function that returns a list of output file extensions that can be handled by an object
    Args:
        object -- The name of the object
    Returns:
        An ordered list of file extensions
    """
    List = []
    geode_object_dict = objects_list()

    values = geode_object_dict[object]["output"]
    for value in values:
        list_creators = value.list_creators()
        for creator in list_creators:
            if creator not in List:
                List.append(creator)
    List.sort()
    return List


def get_versions(list_packages: list):
    list_with_versions = []
    for package in list_packages:
        list_with_versions.append(
            {
                "package": package,
                "version": pkg_resources.get_distribution(package).version,
            }
        )
    return list_with_versions


def upload_file(file: str, file_name: str, upload_folder: str, file_size: int):
    if not os.path.exists(upload_folder):
        os.mkdir(upload_folder)
    file_decoded = base64.b64decode(file.split(",")[-1])
    secure_file_name = werkzeug.utils.secure_filename(file_name)
    file_path = os.path.join(upload_folder, secure_file_name)
    f = open(file_path, "wb")
    f.write(file_decoded)
    f.close()

    final_size = os.path.getsize(file_path)
    uploaded_file = int(file_size) == int(final_size)
    if not uploaded_file:
        flask.abort(500, "File not uploaded")


def create_lock_file(
    folder_absolute_path,
):
    if not os.path.exists(folder_absolute_path):
        os.mkdir(folder_absolute_path)
    id = uuid.uuid4()
    file_absolute_path = f"{folder_absolute_path}/{str(id)}.txt"
    f = open(file_absolute_path, "a")
    f.close()
    flask.g.UUID = id


def create_time_file(folder_absolute_path):
    if not os.path.exists(folder_absolute_path):
        os.mkdir(folder_absolute_path)
    file_path = f"{folder_absolute_path}/time.txt"
    if not os.path.isfile(file_path):
        f = open(file_path, "w")
        f.close()

    f = open(folder_absolute_path + "/time.txt", "w")
    f.write(str(time.time()))
    f.close()


def remove_lock_file(folder_absolute_path):
    id = flask.g.UUID
    os.remove(f"{folder_absolute_path}/{str(id)}.txt")


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.daemon = True
    t.start()
    return t


def is_model(geode_object):
    return objects_list()[geode_object]["is_model"]


def is_3D(geode_object):
    return objects_list()[geode_object]["is_3D"]


def get_builder(geode_object, data):
    return objects_list()[geode_object]["builder"](data)


def get_inspector(geode_object, data):
    return objects_list()[geode_object]["inspector"](data)


def load(geode_object, file_absolute_path):
    return objects_list()[geode_object]["load"](file_absolute_path)


def save(data, geode_object, folder_absolute_path, filename):
    objects_list()[geode_object]["save"](
        data, os.path.join(folder_absolute_path, filename)
    )


def save_viewable(data, geode_object, folder_absolute_path, id):
    return objects_list()[geode_object]["save_viewable"](
        data, os.path.join(folder_absolute_path, id)
    )


def get_form_variables(form, variables_array):
    variables_dict = {}

    for variable in variables_array:
        if form.get(variable) is None:
            flask.abort(400, f"No {variable} sent")
        else:
            variables_dict[variable] = form.get(variable)
    return variables_dict


def get_geographic_coordinate_systems(geode_object):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystem3D.geographic_coordinate_systems()
    else:
        return og_gs.GeographicCoordinateSystem2D.geographic_coordinate_systems()


def get_geographic_coordinate_systems_info(geode_object, crs):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystemInfo3D(
            crs["authority"], crs["code"], crs["name"]
        )
    else:
        return og_gs.GeographicCoordinateSystemInfo2D(
            crs["authority"], crs["code"], crs["name"]
        )


def get_coordinate_system(geode_object, coordinate_system):
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


def assign_geographic_coordinate_system_info(geode_object, data, input_crs):
    builder = get_builder(geode_object, data)
    info = get_geographic_coordinate_systems_info(geode_object, input_crs)
    objects_list()[geode_object]["crs"]["assign"](
        data, builder, input_crs["name"], info
    )


def convert_geographic_coordinate_system_info(geode_object, data, output_crs):
    builder = get_builder(geode_object, data)
    info = get_geographic_coordinate_systems_info(geode_object, output_crs)
    objects_list()[geode_object]["crs"]["convert"](
        data, builder, output_crs["name"], info
    )


def create_coordinate_system(
    geode_object, data, name, input_coordinate_points, output_coordinate_points
):
    builder = get_builder(geode_object, data)

    input_coordiante_system = get_coordinate_system(
        geode_object, input_coordinate_points
    )
    output_coordiante_system = get_coordinate_system(
        geode_object, output_coordinate_points
    )
    objects_list()[geode_object]["crs"]["create"](
        data, builder, name, input_coordiante_system, output_coordiante_system
    )

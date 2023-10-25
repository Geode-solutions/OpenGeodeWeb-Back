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
from .geode_objects import geode_objects_dict


def geode_object_value(geode_object: str):
    return geode_objects_dict()[geode_object]


def input_factory(geode_object: str):
    return geode_object_value(geode_object)["input_factory"]


def output_factory(geode_object: str):
    return geode_object_value(geode_object)["output_factory"]


def missing_files(geode_object: str, file_absolute_path: str):
    return geode_object_value(geode_object)["missing_files"](file_absolute_path)


def load(geode_object: str, file_absolute_path: str):
    return geode_object_value(geode_object)["load"](file_absolute_path)


def save(geode_object: str, data, folder_absolute_path: str, filename: str):
    return geode_object_value(geode_object)["save"](
        data, os.path.join(folder_absolute_path, filename)
    )


def create_builder(geode_object: str, data):
    return geode_object_value(geode_object)["builder"](data)


def assign_crs(geode_object: str, data, crs_name: str, info):
    builder = create_builder(geode_object, data)
    geode_object_value(geode_object)["crs"]["assign"](data, builder, crs_name, info)


def convert_crs(geode_object: str, data, crs_name: str, info):
    builder = create_builder(geode_object, data)
    geode_object_value(geode_object)["crs"]["convert"](data, builder, crs_name, info)


def create_crs(
    geode_object: str,
    data,
    name: str,
    input_coordiante_system,
    output_coordiante_system,
):
    builder = create_builder(geode_object, data)
    geode_object_value(geode_object)["crs"]["create"](
        data, builder, name, input_coordiante_system, output_coordiante_system
    )


def is_model(geode_object: str):
    return geode_object_value(geode_object)["is_model"]


def is_3D(geode_object: str):
    return geode_object_value(geode_object)["is_3D"]


def is_viewable(geode_object: str):
    return geode_object_value(geode_object)["is_viewable"]


def inspector(geode_object: str, data):
    return geode_object_value(geode_object)["inspector"](data)


def save_viewable(geode_object: str, data, folder_absolute_path: str, id: str):
    return geode_object_value(geode_object)["save_viewable"](
        data, os.path.join(folder_absolute_path, id)
    )


def geode_object_input_extensions(geode_object: str):
    geode_object_input_list_creators = input_factory(geode_object).list_creators()
    geode_object_input_list_creators.sort()
    return geode_object_input_list_creators


def geode_object_output_extensions(geode_object: str):
    geode_object_output_list_creators = output_factory(geode_object).list_creators()
    geode_object_output_list_creators.sort()
    return geode_object_output_list_creators


def list_input_extensions(key: str = None):
    extensions_list = []
    for geode_object, value in geode_objects_dict().items():
        if key != None:
            if key in value:
                if type(value[key]) == bool:
                    if value[key] == True:
                        extensions_list += geode_object_input_extensions(geode_object)
                else:
                    extensions_list += geode_object_input_extensions(geode_object)
        else:
            extensions_list += geode_object_input_extensions(geode_object)

    extensions_list = list(set(extensions_list))
    extensions_list.sort()
    return extensions_list


def has_creator(geode_object: str, extension: str):
    return input_factory(geode_object).has_creator(extension)


def list_geode_objects(extension: str, key: str = None):
    geode_objects_list = []
    for geode_object, value in geode_objects_dict().items():
        if key != None:
            if key in value:
                if type(value[key]) == bool:
                    if value[key] == True:
                        if has_creator(geode_object, extension):
                            geode_objects_list.append(geode_object)
                elif has_creator(geode_object, extension):
                    geode_objects_list.append(geode_object)
        else:
            if has_creator(geode_object, extension):
                geode_objects_list.append(geode_object)

    geode_objects_list.sort()
    return geode_objects_list


def geode_objects_output_extensions(geode_object: str):
    return_list = []
    geode_object_dict = {}
    geode_object_dict["geode_object"] = geode_object
    geode_object_dict["output_extensions"] = geode_object_output_extensions(
        geode_object
    )

    return_list.append(geode_object_dict)

    if "parent" in geode_object_value(geode_object).keys():
        parent_key = geode_object_value(geode_object)["parent"]
        return_list += geode_objects_output_extensions(parent_key)

    return return_list


def versions(list_packages: list):
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


def extension_from_filename(filename):
    return os.path.splitext(filename)[1][1:]


def form_variables(form, variables_array):
    variables_dict = {}
    for variable in variables_array:
        if form.get(variable) is None:
            flask.abort(400, f"No {variable} sent")
        else:
            variables_dict[variable] = form.get(variable)
    return variables_dict


def geographic_coordinate_systems(geode_object: str):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystem3D.geographic_coordinate_systems()
    else:
        return og_gs.GeographicCoordinateSystem2D.geographic_coordinate_systems()


def geographic_coordinate_systems_info(geode_object: str, crs):
    if is_3D(geode_object):
        return og_gs.GeographicCoordinateSystemInfo3D(
            crs["authority"], crs["code"], crs["name"]
        )
    else:
        return og_gs.GeographicCoordinateSystemInfo2D(
            crs["authority"], crs["code"], crs["name"]
        )


def coordinate_system(geode_object: str, coordinate_system):
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


def assign_geographic_coordinate_system_info(geode_object: str, data, input_crs):
    info = geographic_coordinate_systems_info(geode_object, input_crs)
    assign_crs(geode_object, data, input_crs["name"], info)


def convert_geographic_coordinate_system_info(geode_object: str, data, output_crs):
    info = geographic_coordinate_systems_info(geode_object, output_crs)
    convert_crs(geode_object, data, output_crs["name"], info)


def create_coordinate_system(
    geode_object: str, data, name, input_coordinate_points, output_coordinate_points
):
    input_coordiante_system = coordinate_system(geode_object, input_coordinate_points)
    output_coordiante_system = coordinate_system(geode_object, output_coordinate_points)
    create_crs(
        geode_object, data, name, input_coordiante_system, output_coordiante_system
    )

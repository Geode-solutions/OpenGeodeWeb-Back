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
from jsonschema import validate
from jsonschema.exceptions import ValidationError

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


def is_saveable(geode_object: str, data, filename: str):
    return geode_object_value(geode_object)["is_saveable"](data, filename)


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


def geode_objects_output_extensions(geode_object: str, data):
    geode_objects_output_extensions_dict = {}
    output_extensions = geode_object_output_extensions(geode_object)
    extensions_dict = {}
    for output_extension in output_extensions:
        bool_is_saveable = is_saveable(geode_object, data, f"test.{output_extension}")
        extensions_dict[output_extension] = {"is_saveable": bool_is_saveable}
    geode_objects_output_extensions_dict[geode_object] = extensions_dict

    if "parent" in geode_object_value(geode_object).keys():
        parent_geode_object = geode_object_value(geode_object)["parent"]
        geode_objects_output_extensions_dict.update(
            geode_objects_output_extensions(parent_geode_object, data)
        )
    return geode_objects_output_extensions_dict


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


def validate_request(request, schema):
    json_data = request.get_json(force=True, silent=True)

    if json_data is None:
        json_data = {}

    try:
        validate(instance=json_data, schema=schema)
    except ValidationError as e:
        flask.abort(400, f"Validation error: {e.message}")


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


def send_file(upload_folder, saved_files, new_file_name):
    if len(saved_files) == 1:
        mimetype = "application/octet-binary"
    else:
        mimetype = "application/zip"
        new_file_name = strict_file_name + ".zip"
        with zipfile.ZipFile(os.path.join(upload_folder, new_file_name), "w") as zipObj:
            for saved_file_path in saved_files:
                zipObj.write(
                    saved_file_path,
                    os.path.basename(saved_file_path),
                )

    response = flask.send_from_directory(
        directory=upload_folder,
        path=new_file_name,
        as_attachment=True,
        mimetype=mimetype,
    )
    response.headers["new-file-name"] = new_file_name
    response.headers["Access-Control-Expose-Headers"] = "new-file-name"

    return response

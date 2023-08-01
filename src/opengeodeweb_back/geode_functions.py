# Standard library imports
import base64
import os
import uuid

# Third party imports
import flask
import opengeode_geosciences as og_gs
import opengeode as og
import pkg_resources
import werkzeug

# Local application imports
from .geode_objects import objects_list


def list_objects_input_extensions(
    is_viewable: bool = True,
    geode_object: str = "",
):
    """
    Purpose:
        Function that returns a list of all input extensions
    Returns:
        An ordered list of input file extensions
    """
    return_list = []
    objects_list = geode_objects.objects_list()

    for object_ in objects_list.values():
        if object_["is_viewable"] == is_viewable or geode_object == object_:
            values = object_["input"]
            for value in values:
                list_creators = value.list_creators()
                for creator in list_creators:
                    if creator not in return_list:
                        return_list.append(creator)
    return_list.sort()
    return return_list


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
    objects_list = geode_objects.objects_list()

    for object_, values in objects_list.items():
        if values["is_viewable"] == is_viewable:
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
    objects_list = geode_objects.objects_list()

    values = objects_list[object]["output"]
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
    return int(file_size) == int(final_size)


def create_lock_file():
    LOCK_FOLDER = flask.current_app.config["LOCK_FOLDER"]
    if not os.path.exists(LOCK_FOLDER):
        os.mkdir(LOCK_FOLDER)
    flask.g.UUID = uuid.uuid4()
    file_path = f"{LOCK_FOLDER}/{str(flask.g.UUID)}.txt"
    f = open(file_path, "a")
    f.close()


def remove_lock_file():
    LOCK_FOLDER = flask.current_app.config["LOCK_FOLDER"]
    os.remove(f"{LOCK_FOLDER}/{str(flask.g.UUID)}.txt")


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()

    t = threading.Timer(sec, func_wrapper)
    t.daemon = True
    t.start()
    return t


def is_model(geode_object):
    return geode_objects.objects_list()[geode_object]["is_model"]


def is_3D(geode_object):
    return geode_objects.objects_list()[geode_object]["is_3D"]


def get_builder(geode_object, data):
    return geode_objects.objects_list()[geode_object]["builder"](data)


def load(file_path):
    return geode_objects.objects_list()[geode_object]["load"](file_path)


def save(data, geode_object, folder, filename):
    geode_objects.objects_list()[geode_object]["save"](
        data, os.path.join(folder, filename)
    )


def save_viewable(data, geode_object, folder, id):
    geode_objects.objects_list()[geode_object]["save_viewable"](
        data, os.path.join(folder, id)
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
    geode_objects.objects_list()[geode_object]["crs"]["assign"](
        data, builder, input_crs["name"], info
    )


def convert_geographic_coordinate_system_info(geode_object, data, output_crs):
    builder = get_builder(geode_object, data)
    info = get_geographic_coordinate_systems_info(geode_object, output_crs)
    geode_objects.objects_list()[geode_object]["crs"]["convert"](
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
    geode_objects.objects_list()[geode_object]["crs"]["create"](
        data, builder, name, input_coordiante_system, output_coordiante_system
    )

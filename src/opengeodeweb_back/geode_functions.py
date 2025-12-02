# Standard library imports
import os

# Third party imports
import werkzeug
import flask

# Local application imports
from .geode_objects import geode_objects
from .geode_objects.types import (
    GeodeObjectType,
    geode_object_type,
)
from .geode_objects.geode_object import GeodeObject
from opengeodeweb_microservice.database.data import Data


def data_file_path(data_id: str, filename: str | None = None) -> str:
    data_folder_path = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = os.path.join(data_folder_path, data_id)
    if filename is not None:
        return os.path.join(data_path, filename)
    return data_path


def geode_object_from_string(value: str) -> type[GeodeObject]:
    return geode_objects[geode_object_type(value)]


def load_geode_object(data_id: str) -> GeodeObject:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data.native_file)
    print("Loading file: ", file_absolute_path)
    print("File exists: ", os.path.exists(file_absolute_path))
    return geode_object_from_string(data.geode_object).load(file_absolute_path)


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

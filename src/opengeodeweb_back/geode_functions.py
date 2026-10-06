from __future__ import annotations

# Standard library imports
import logging
from pathlib import Path
from typing import TYPE_CHECKING

# Third party imports
import flask
import werkzeug
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.data_types import (
    GeodeObjectType,
    geode_object_type,
)

# Local application imports
from .geode_objects import geode_objects

if TYPE_CHECKING:
    from .geode_objects.geode_object import GeodeObject


logger = logging.getLogger(__name__)


def data_file_path(data_id: str, filename: str | None = None) -> str:
    data_folder_path = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = Path(data_folder_path) / data_id
    if filename is not None:
        return str(data_path / filename)
    return str(data_path)


def geode_object_from_string(value: str) -> type[GeodeObject]:
    return geode_objects[geode_object_type(value)]


def load_geode_object(data_id: str) -> GeodeObject:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")

    file_absolute_path = data_file_path(data_id, data.native_file)
    logger.debug(
        "Loading file: %s (exists: %s)", file_absolute_path, Path(file_absolute_path).exists()
    )
    return geode_object_from_string(data.geode_object).load(file_absolute_path)


def get_data_info(data_id: str) -> Data:
    data = Data.get(data_id)
    if not data:
        flask.abort(404, f"Data with id {data_id} not found")
    return data


def upload_file_path(filename: str) -> str:
    upload_folder = flask.current_app.config["UPLOAD_FOLDER_PATH"]
    secure_filename = werkzeug.utils.secure_filename(filename)
    return str((Path(upload_folder) / secure_filename).resolve())


def geode_object_output_extensions(
    geode_object: GeodeObject,
) -> dict[GeodeObjectType, dict[str, bool]]:
    results: dict[GeodeObjectType, dict[str, bool]] = {}
    for mixin_geode_object in geode_objects[geode_object.geode_object_type()].__mro__:
        output_extensions_method = getattr(mixin_geode_object, "output_extensions", None)
        if output_extensions_method is None:
            continue
        output_extensions = output_extensions_method.__func__(mixin_geode_object)
        if output_extensions is None:
            continue
        object_output_extensions: dict[str, bool] = {}
        is_saveable_method = mixin_geode_object.is_saveable  # type: ignore[attr-defined]
        for output_extension in output_extensions:
            bool_is_saveable = is_saveable_method(geode_object, f"test.{output_extension}")
            object_output_extensions[output_extension] = bool_is_saveable
        if hasattr(mixin_geode_object, "geode_object_type"):
            results[mixin_geode_object.geode_object_type()] = object_output_extensions
    return results

from __future__ import annotations

# Standard library imports
import base64
import hashlib
import logging
import threading
import time
import uuid
import zipfile
from concurrent.futures import ThreadPoolExecutor
from importlib import metadata
from pathlib import Path
from typing import TYPE_CHECKING, Any

import fastjsonschema  # type: ignore[import-untyped]

# Third party imports
import flask
import opengeode as og
from defusedxml.ElementTree import parse
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.schemas import ErrorResponse, SchemaDict

# Local application imports
from . import geode_functions
from .geode_objects import geode_objects
from .geode_objects.geode_model import GeodeModel
from .geode_objects.geode_vertex_set import GeodeVertexSet

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Callable

    from opengeodeweb_microservice.database.data_types import GeodeObjectType
    from werkzeug.exceptions import HTTPException

    from .geode_objects.geode_object import GeodeObject


def increment_request_counter(current_app: flask.Flask) -> None:
    if "REQUEST_COUNTER" in current_app.config:
        request_counter = int(current_app.config.get("REQUEST_COUNTER", 0))
        request_counter += 1
        current_app.config.update(REQUEST_COUNTER=request_counter)


def decrement_request_counter(current_app: flask.Flask) -> None:
    if "REQUEST_COUNTER" in current_app.config:
        request_counter = int(current_app.config.get("REQUEST_COUNTER", 0))
        request_counter -= 1
        current_app.config.update(REQUEST_COUNTER=request_counter)


def update_last_request_time(current_app: flask.Flask) -> None:
    if "LAST_REQUEST_TIME" in current_app.config:
        current_app.config.update(LAST_REQUEST_TIME=time.time())


def terminate_session(exception: BaseException | None) -> None:
    session = flask.g.pop("session", None)
    if session is None:
        return
    if exception is None:
        session.commit()
    else:
        session.rollback()
    session.close()


def before_request(current_app: flask.Flask) -> None:
    increment_request_counter(current_app)
    flask.g.session = get_session()
    flask.g.start_time = time.perf_counter()


def teardown_request(current_app: flask.Flask, exception: BaseException | None = None) -> None:
    decrement_request_counter(current_app)
    update_last_request_time(current_app)
    terminate_session(exception)
    if flask.has_request_context():
        if hasattr(flask.g, "start_time"):
            duration = time.perf_counter() - flask.g.start_time
            logger.info("Request to %s completed in %.3fs", flask.request.endpoint, duration)
        else:
            logger.info("Request to %s completed", flask.request.endpoint)


def kill_task(current_app: flask.Flask) -> bool:
    request_counter = int(current_app.config.get("REQUEST_COUNTER", 0))
    last_ping_time = float(current_app.config.get("LAST_PING_TIME", 0))
    last_request_time = float(current_app.config.get("LAST_REQUEST_TIME", 0))
    minutes_before_timeout = float(current_app.config.get("MINUTES_BEFORE_TIMEOUT", 0))
    current_time = time.time()
    minutes_since_last_request = (current_time - last_request_time) / 60
    minutes_since_last_ping = (current_time - last_ping_time) / 60
    logger.debug(
        "kill_task: request_counter=%s minutes_before_timeout=%s "
        "minutes_since_last_ping=%s minutes_since_last_request=%s",
        request_counter,
        minutes_before_timeout,
        minutes_since_last_ping,
        minutes_since_last_request,
    )
    if request_counter > 1:
        return False
    if minutes_before_timeout == 0:
        return False
    if minutes_since_last_ping > minutes_before_timeout:
        return True
    return minutes_since_last_request > minutes_before_timeout


def versions(list_packages: list[str]) -> list[dict[str, str]]:
    return [
        {"package": package, "version": metadata.distribution(package).version}
        for package in list_packages
    ]


def validate_request(request: flask.Request, schema: SchemaDict) -> dict[str, Any]:
    json_data = request.get_json(force=True, silent=True)

    if json_data is None:
        json_data = {}
    try:
        validate = fastjsonschema.compile(schema)
        validate(json_data)
    except fastjsonschema.JsonSchemaException as e:
        error_msg = str(e)
        logger.warning("Validation failed: %s", error_msg)
        flask.abort(400, error_msg)
    return json_data


def set_interval(
    function: Callable[[flask.Flask], None], seconds: float, args: flask.Flask
) -> threading.Timer:
    def function_wrapper() -> None:
        set_interval(function, seconds, args)
        function(args)

    timer = threading.Timer(seconds, function_wrapper)
    timer.daemon = True
    timer.start()
    return timer


def extension_from_filename(filename: str) -> str:
    return Path(filename).suffix[1:]


def send_file(upload_folder: str, saved_files: list[str], new_file_name: str) -> flask.Response:
    if len(saved_files) == 1:
        mimetype = "application/octet-binary"
    else:
        mimetype = "application/zip"
        new_file_name = Path(new_file_name).stem + ".zip"
        with zipfile.ZipFile(Path(upload_folder).resolve() / new_file_name, "w") as zip_file:
            for saved_file_path in saved_files:
                zip_file.write(
                    saved_file_path,
                    Path(saved_file_path).name,
                )

    response = flask.send_from_directory(
        directory=Path(upload_folder).resolve(),
        path=new_file_name,
        as_attachment=True,
        mimetype=mimetype,
    )
    response.headers["new-file-name"] = new_file_name
    response.headers["Access-Control-Expose-Headers"] = "new-file-name"

    return response


def handle_exception(exception: HTTPException) -> flask.Response:
    logger.error("Error: %s", exception)
    code = exception.code or 500
    error = ErrorResponse(
        code=code,
        name=exception.name,
        description=exception.description or "An error occurred",
    )
    response = flask.jsonify(error.to_dict())
    response.content_type = "application/json"
    response.status_code = code
    return response


def handle_unexpected_exception(exception: Exception) -> flask.Response:
    logger.error("Unexpected error: %s", exception, exc_info=exception)
    error = ErrorResponse(code=500, name="Internal Server Error", description=str(exception))
    return flask.make_response(error.to_dict(), 500)


def create_data_folder_from_id(data_id: str) -> str:
    base_data_folder = flask.current_app.config["DATA_FOLDER_PATH"]
    data_path = Path(base_data_folder) / data_id
    data_path.mkdir(parents=True, exist_ok=True)
    return str(data_path)


def content_based_uuid(file_path: str) -> og.uuid:
    with Path(file_path).open("rb") as file:
        digest = hashlib.file_digest(file, "sha256").hexdigest()
    return og.uuid(str(uuid.uuid5(uuid.NAMESPACE_OID, digest)))


def _uuid_to_flat_index(data_id: str, viewable_file: str | None) -> dict[str, int]:
    uuid_to_flat_index: dict[str, int] = {}
    if viewable_file:
        vtm_file_path = geode_functions.data_file_path(data_id, viewable_file)
        tree = parse(vtm_file_path)
        root = tree.find("vtkMultiBlockDataSet")
        if root is None:
            flask.abort(500, "Failed to read viewable file")
        for current_index, elem in enumerate(root.iter()):
            if "uuid" in elem.attrib and elem.tag == "DataSet":
                uuid_to_flat_index[elem.attrib["uuid"]] = current_index
    return uuid_to_flat_index


def _mesh_components(model: GeodeModel, uuid_to_flat_index: dict[str, int]) -> list[dict[str, Any]]:
    model_mesh_components = model.mesh_components()
    mesh_components = []
    for mesh_component, ids in model_mesh_components.items():
        component_type = mesh_component.get()
        for component_id in ids:
            component = model.component(component_id)
            geode_id = component_id.string()
            component_name = component.name()
            if not component_name:
                component_name = geode_id
            viewer_id = uuid_to_flat_index[geode_id]
            boundaries = model.boundaries(component_id)
            boundaries_uuid = [boundary.id.string() for boundary in boundaries]
            internals = model.internals(component_id)
            internals_uuid = [internal.id.string() for internal in internals]
            mesh_component_object = {
                "viewer_id": viewer_id,
                "geode_id": geode_id,
                "name": component_name,
                "type": component_type,
                "boundaries": boundaries_uuid,
                "internals": internals_uuid,
                "is_active": component.is_active(),
            }
            mesh_components.append(mesh_component_object)
    return mesh_components


def _collection_components(model: GeodeModel) -> list[dict[str, Any]]:
    model_collection_components = model.collection_components()
    collection_components = []
    for collection_component, ids in model_collection_components.items():
        component_type = collection_component.get()
        for component_id in ids:
            component = model.component(component_id)
            geode_id = component_id.string()
            component_name = component.name()
            if not component_name:
                component_name = geode_id
            items = model.items(component_id)
            items_uuid = [item.id.string() for item in items]
            collection_component_object = {
                "geode_id": geode_id,
                "name": component_name,
                "type": component_type,
                "items": items_uuid,
                "is_active": component.is_active(),
            }
            collection_components.append(collection_component_object)
    return collection_components


def model_components(data_id: str, model: GeodeModel, viewable_file: str | None) -> dict[str, Any]:
    uuid_to_flat_index = _uuid_to_flat_index(data_id, viewable_file)
    return {
        "mesh_components": _mesh_components(model, uuid_to_flat_index),
        "collection_components": _collection_components(model),
    }


def save_all_viewables_and_return_info(
    geode_object: GeodeObject,
    data: Data,
    data_path: str,
) -> dict[str, Any]:
    with ThreadPoolExecutor() as executor:
        tasks: list[tuple[Callable[[str], Any], str]] = [
            (
                geode_object.save,
                str(Path(data_path) / ("native." + geode_object.native_extension())),
            )
        ]
        if geode_object.is_viewable():
            tasks.extend(
                [
                    (geode_object.save_viewable, str(Path(data_path) / "viewable")),
                    (
                        geode_object.save_light_viewable,
                        str(Path(data_path) / "light_viewable"),
                    ),
                ]
            )

        results = list(executor.map(lambda args: args[0](args[1]), tasks))
        native_files = results[0]
        if geode_object.is_viewable():
            viewable_path = results[1]
            light_path = results[2]
            binary_light_viewable = Path(light_path).read_bytes()
            binary_light_viewable_str = base64.b64encode(binary_light_viewable).decode("ascii")
            data.viewable_file = Path(viewable_path).name
            data.light_viewable_file = Path(light_path).name
        else:
            binary_light_viewable_str = None
            data.viewable_file = None
            data.light_viewable_file = None

        data.native_file = Path(native_files[0]).name

        name = geode_object.identifier.name()
        if not name:
            flask.abort(400, "Geode object has no name defined.")

        response: dict[str, Any] = {
            "native_file": data.native_file,
            "id": data.id,
            "geode_id": data.geode_id,
            "name": name,
            "viewer_type": data.viewer_object,
            "is_viewable": geode_object.is_viewable(),
            "geode_object_type": data.geode_object,
        }
        if geode_object.is_viewable():
            response["viewable_file"] = data.viewable_file
            response["binary_light_viewable"] = binary_light_viewable_str
        if isinstance(geode_object, GeodeVertexSet):
            response["nb_vertices"] = geode_object.vertex_set.nb_vertices()
        if isinstance(geode_object, GeodeModel):
            response |= model_components(data.id, geode_object, data.viewable_file)
        return response


def generate_files_from_object(
    geode_object: GeodeObject,
) -> dict[str, Any]:
    data = Data.create(
        geode_id=geode_object.identifier.id().string(),
        geode_object=geode_object.geode_object_type(),
        viewer_object=geode_object.viewer_type(),
        viewer_elements_type=geode_object.viewer_elements_type(),
    )
    data_path = create_data_folder_from_id(data.id)
    return save_all_viewables_and_return_info(geode_object, data, data_path)


def generate_files_from_file(geode_object_type: GeodeObjectType, input_file: str) -> dict[str, Any]:
    generic_geode_object = geode_objects[geode_object_type]
    full_input_filename = geode_functions.upload_file_path(input_file)
    geode_object = generic_geode_object.load(full_input_filename)
    geode_object.builder().set_name(Path(input_file).stem)
    if not input_file.lower().endswith("." + geode_object.native_extension()):
        geode_object.builder().set_id(content_based_uuid(full_input_filename))
    data = Data.create(
        geode_id=geode_object.identifier.id().string(),
        geode_object=geode_object_type,
        viewer_object=generic_geode_object.viewer_type(),
        viewer_elements_type=generic_geode_object.viewer_elements_type(),
    )
    data_path = create_data_folder_from_id(data.id)
    return save_all_viewables_and_return_info(geode_object, data, data_path)

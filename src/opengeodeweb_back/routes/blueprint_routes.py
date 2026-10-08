from __future__ import annotations

# Standard library imports
import logging
import math
import os
import shutil
import time
import typing
import zipfile
from pathlib import Path
from threading import Timer
from typing import TYPE_CHECKING

# Third party imports
import flask
import opengeode as og
import opengeode_geosciences as og_geosciences
import opengeode_geosciencesio as og_geosciencesio  # noqa: F401 (registers IO plugins)
import opengeode_io as og_io  # noqa: F401 (registers IO plugins)
import werkzeug
from opengeodeweb_microservice.database import connection
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.data_types import geode_object_type
from sqlalchemy.exc import OperationalError

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.geode_objects import geode_objects
from opengeodeweb_back.geode_objects.geode_graph import GeodeGraph
from opengeodeweb_back.geode_objects.geode_grid2d import GeodeGrid2D
from opengeodeweb_back.geode_objects.geode_grid3d import GeodeGrid3D
from opengeodeweb_back.geode_objects.geode_mesh import GeodeMesh
from opengeodeweb_back.geode_objects.geode_model import GeodeModel
from opengeodeweb_back.geode_objects.geode_solid_mesh3d import GeodeSolidMesh3D
from opengeodeweb_back.geode_objects.geode_surface_mesh2d import GeodeSurfaceMesh2D
from opengeodeweb_back.geode_objects.geode_surface_mesh3d import GeodeSurfaceMesh3D
from opengeodeweb_back.routes import schemas
from opengeodeweb_back.typed_route import parse_params, raw_route, typed_route

if TYPE_CHECKING:
    from werkzeug.datastructures import FileStorage

ComponentMesh = (
    og.Corner2D,
    og.Corner3D,
    og.Line2D,
    og.Line3D,
    og.Surface2D,
    og.Surface3D,
    og.Block3D,
)
ComponentLine = (og.Line2D, og.Line3D)
ComponentSurface = (og.Surface2D, og.Surface3D)
ComponentBlock = og.Block3D

logger = logging.getLogger(__name__)

routes = flask.Blueprint("routes", __name__, url_prefix="/opengeodeweb_back")


@typed_route(routes, schemas.allowed_files_route)
def allowed_files(_params: schemas.AllowedFiles) -> schemas.AllowedFilesResponse:
    extensions: set[str] = set()
    for geode_object in geode_objects.values():
        for extension in geode_object.input_extensions():
            extensions.add(extension)
    return schemas.AllowedFilesResponse(extensions=list(extensions))


def _write_stream(path: Path, stream: typing.IO[bytes], mode: str = "wb") -> None:
    read_buffer_size = 1024 * 1024
    with path.open(mode) as destination:
        while chunk := stream.read(read_buffer_size):
            destination.write(chunk)


def _upload_response(message: str, status: int) -> flask.Response:
    return flask.make_response(schemas.UploadFileResponse(message=message).to_dict(), status)


def _finalize_upload(filename: str) -> flask.Response:
    logger.info("File uploaded: %s", filename)
    return _upload_response("File uploaded", 201)


@raw_route(routes, schemas.upload_file_route)
def upload_file() -> flask.Response:
    upload_folder_path = flask.current_app.config["UPLOAD_FOLDER_PATH"]
    logger.debug("Upload folder: %s", upload_folder_path)
    Path(upload_folder_path).mkdir(parents=True, exist_ok=True)

    # Multipart callers (e.g. Vease) still send the whole file as a "file" form
    # part. Everything else PUTs raw bytes with ?filename= as a query param:
    # either the whole file in one request, or one of several chunks (when
    # ?chunk_index=/?total_chunks= are also present) that get appended in
    # order and assembled into the final file once the last one arrives. This
    # keeps every request under cloud hosting's hard request-size limit.
    if flask.request.mimetype == "multipart/form-data":
        file = flask.request.files["file"]
        if file.filename is None:
            flask.abort(400, "Filename is required")
        filename = werkzeug.utils.secure_filename(Path(file.filename).name)
        file_path = Path(upload_folder_path) / filename
        file.save(file_path)
        return _finalize_upload(filename)

    raw_filename = flask.request.args.get("filename")
    if not raw_filename:
        flask.abort(400, "Filename is required")
    filename = werkzeug.utils.secure_filename(Path(raw_filename).name)
    file_path = Path(upload_folder_path) / filename

    total_chunks = flask.request.args.get("total_chunks", type=int)
    if total_chunks is None:
        _write_stream(file_path, flask.request.stream)
        return _finalize_upload(filename)

    chunk_index = flask.request.args.get("chunk_index", type=int)
    if chunk_index is None or not 0 <= chunk_index < total_chunks:
        flask.abort(400, "Invalid chunk_index")

    part_path = file_path.with_name(f"{file_path.name}.part")
    _write_stream(part_path, flask.request.stream, "wb" if chunk_index == 0 else "ab")
    if chunk_index < total_chunks - 1:
        return _upload_response("Chunk received", 200)

    part_path.replace(file_path)
    return _finalize_upload(filename)


@typed_route(routes, schemas.allowed_objects_route)
def allowed_objects(
    params: schemas.AllowedObjects,
) -> schemas.AllowedObjectsResponse:
    file_absolute_path = geode_functions.upload_file_path(params.filename)
    file_extension = utils_functions.extension_from_filename(Path(file_absolute_path).name)
    allowed_objects: dict[str, schemas.allowed_objects.AllowedObject] = {}
    for object_type, geode_object in geode_objects.items():
        if file_extension not in geode_object.input_extensions():
            continue
        loadability_score = geode_object.is_loadable(file_absolute_path)
        priority_score = geode_object.object_priority(file_absolute_path)
        allowed_objects[object_type] = schemas.allowed_objects.AllowedObject(
            is_loadable=loadability_score.value(),
            object_priority=priority_score,
        )
    return schemas.AllowedObjectsResponse(allowed_objects=allowed_objects)


@typed_route(routes, schemas.missing_files_route)
def missing_files(params: schemas.MissingFiles) -> schemas.MissingFilesResponse:
    file_path = geode_functions.upload_file_path(params.filename)
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type)
    additional_files = geode_object.additional_files(
        file_path,
    )
    has_missing_files = any(
        file.is_missing
        for file in additional_files.mandatory_files + additional_files.optional_files
    )
    mandatory_files = [
        Path(file.filename).name for file in additional_files.mandatory_files if file.is_missing
    ]
    additional_files_array = [
        Path(file.filename).name for file in additional_files.optional_files if file.is_missing
    ]

    return schemas.MissingFilesResponse(
        has_missing_files=has_missing_files,
        mandatory_files=mandatory_files,
        additional_files=additional_files_array,
    )


@typed_route(routes, schemas.geographic_coordinate_systems_route)
def crs_converter_geographic_coordinate_systems(
    params: schemas.GeographicCoordinateSystems,
) -> schemas.GeographicCoordinateSystemsResponse:
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type)
    infos = (
        og_geosciences.GeographicCoordinateSystem3D.geographic_coordinate_systems()
        if geode_object.is_3d()
        else og_geosciences.GeographicCoordinateSystem2D.geographic_coordinate_systems()
    )
    crs_list = [
        schemas.geographic_coordinate_systems.CRSList(
            name=info.name, code=info.code, authority=info.authority
        )
        for info in infos
    ]
    return schemas.GeographicCoordinateSystemsResponse(crs_list=crs_list)


@typed_route(routes, schemas.validate_route)
def validate_object(params: schemas.Validate) -> schemas.ValidateResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    validity = geode_object.validate()
    return schemas.ValidateResponse(
        is_valid=validity.nb_issues() == 0,
        nb_issues=validity.nb_issues(),
        issues=validity.invalidities,
    )


@typed_route(routes, schemas.geode_objects_and_output_extensions_route)
def geode_objects_and_output_extensions(
    params: schemas.GeodeObjectsAndOutputExtensions,
) -> schemas.GeodeObjectsAndOutputExtensionsResponse:
    file_path = geode_functions.upload_file_path(params.filename)
    geode_object = geode_functions.geode_object_from_string(params.geode_object_type).load(
        file_path
    )
    geode_objects_and_output_extensions = geode_functions.geode_object_output_extensions(
        geode_object
    )
    return schemas.GeodeObjectsAndOutputExtensionsResponse(
        geode_objects_and_output_extensions={
            str(object_type): extensions
            for object_type, extensions in geode_objects_and_output_extensions.items()
        }
    )


@typed_route(routes, schemas.save_viewable_file_route)
def save_viewable_file(
    params: schemas.SaveViewableFile,
) -> schemas.SaveViewableFileResponse:
    return schemas.SaveViewableFileResponse.from_dict(
        utils_functions.generate_files_from_file(
            geode_object_type=geode_object_type(params.geode_object_type),
            input_file=params.filename,
        )
    )


@typed_route(routes, schemas.texture_coordinates_route)
def texture_coordinates(
    params: schemas.TextureCoordinates,
) -> schemas.TextureCoordinatesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeSurfaceMesh2D | GeodeSurfaceMesh3D):
        flask.abort(400, f"{params.id} is not a GeodeSurfaceMesh")
    texture_coordinates = geode_object.texture_manager().texture_names()
    return schemas.TextureCoordinatesResponse(texture_coordinates=texture_coordinates)


def extract_valid_attribute_values(
    attribute_manager: og.AttributeManager,
    attribute_name: str,
    item_index: int,
) -> tuple[list[float], bool]:
    attribute_ids = attribute_manager.attribute_ids_matching_name(attribute_name)
    if not isinstance(attribute_ids, list):
        return [], False
    attribute = attribute_manager.find_generic_attribute(attribute_ids[0])
    if (
        attribute is None
        or not attribute.is_genericable()
        or not attribute.properties().transferable
    ):
        return [], False

    nb_items = attribute.nb_items()
    default_values = getattr(attribute, "default_values", None)
    no_value = default_values().no_value if default_values else None
    if no_value is None and ("Point" in attribute.type() or "Vector" in attribute.type()):
        no_value = [0.0] * nb_items

    value_getter = getattr(
        attribute,
        "value",
        lambda element_index: [
            attribute.generic_item_value(element_index, i) for i in range(nb_items)
        ],
    )

    valid_values: list[float] = []
    has_nan = False
    for element_index in range(attribute_manager.nb_elements()):
        value = attribute.generic_item_value(element_index, item_index)
        if (
            value is None
            or math.isnan(value)
            or (no_value is not None and value_getter(element_index) == no_value)
        ):
            has_nan = True
        else:
            valid_values.append(value)
    return valid_values, has_nan


def attributes_metadata(
    manager: og.AttributeManager | list[og.AttributeManager],
) -> list[dict[str, str | int | float | bool | list[float]]]:
    attribute_managers = manager if isinstance(manager, list) else [manager]
    attributes: list[dict[str, str | int | float | bool | list[float]]] = []
    first_manager = attribute_managers[0]
    for attribute_id in first_manager.attribute_ids():
        attribute = first_manager.find_generic_attribute(attribute_id)
        if attribute is None:
            continue
        attribute_name = attribute.name()
        if attribute_name is None:
            continue
        if not attribute.is_genericable() or not attribute.properties().transferable:
            continue
        nb_items = attribute.nb_items()
        min_values, max_values = [], []
        attribute_has_nan = False
        for item_index in range(nb_items):
            valid_values: list[float] = []
            for attribute_manager in attribute_managers:
                extracted_values, has_nan = extract_valid_attribute_values(
                    attribute_manager, attribute_name, item_index
                )
                valid_values.extend(extracted_values)
                if has_nan:
                    attribute_has_nan = True
            if valid_values:
                min_values.append(min(valid_values))
                max_values.append(max(valid_values))
        if not min_values or not max_values:
            continue
        attributes.append(
            {
                "attribute_name": attribute_name,
                "attribute_id": attribute_id.string(),
                "nb_items": nb_items,
                "min_value": min(min_values),
                "max_value": max(max_values),
                "min_values": min_values,
                "max_values": max_values,
                "no_data": attribute_has_nan,
            }
        )
    return attributes


@typed_route(routes, schemas.vertex_attribute_names_route)
def vertex_attribute_names(
    params: schemas.VertexAttributeNames,
) -> schemas.VertexAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeMesh):
        flask.abort(400, f"{params.id} is not a GeodeMesh")
    attribute_manager = geode_object.vertex_attribute_manager()
    return schemas.VertexAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(attribute_manager)}
    )


@typed_route(routes, schemas.cell_attribute_names_route)
def cell_attribute_names(
    params: schemas.CellAttributeNames,
) -> schemas.CellAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeGrid2D | GeodeGrid3D):
        flask.abort(400, f"{params.id} is not a GeodeGrid")
    attribute_manager = geode_object.cell_attribute_manager()
    return schemas.CellAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(attribute_manager)}
    )


@typed_route(routes, schemas.polygon_attribute_names_route)
def polygon_attribute_names(
    params: schemas.PolygonAttributeNames,
) -> schemas.PolygonAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeSurfaceMesh2D | GeodeSurfaceMesh3D):
        flask.abort(400, f"{params.id} is not a GeodeSurfaceMesh")
    attribute_manager = geode_object.polygon_attribute_manager()
    return schemas.PolygonAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(attribute_manager)}
    )


@typed_route(routes, schemas.polyhedron_attribute_names_route)
def polyhedron_attribute_names(
    params: schemas.PolyhedronAttributeNames,
) -> schemas.PolyhedronAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeSolidMesh3D):
        flask.abort(400, f"{params.id} is not a GeodeSolidMesh")
    attribute_manager = geode_object.polyhedron_attribute_manager()
    return schemas.PolyhedronAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(attribute_manager)}
    )


@typed_route(routes, schemas.edge_attribute_names_route)
def edge_attribute_names(
    params: schemas.EdgeAttributeNames,
) -> schemas.EdgeAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeGraph):
        flask.abort(400, f"{params.id} does not have edges")
    attribute_manager = geode_object.edge_attribute_manager()
    return schemas.EdgeAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(attribute_manager)}
    )


@typed_route(routes, schemas.model_component_vertex_attribute_names_route)
def model_component_vertex_attribute_names(
    params: schemas.ModelComponentVertexAttributeNames,
) -> schemas.ModelComponentVertexAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeModel):
        flask.abort(400, f"{params.id} is not a GeodeModel")
    managers = [
        component.mesh().vertex_attribute_manager()
        for component_id in params.component_ids
        if isinstance(
            (component := geode_object.component(og.uuid(component_id))),
            ComponentMesh,
        )
    ]
    return schemas.ModelComponentVertexAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(managers)}
    )


@typed_route(routes, schemas.model_component_edge_attribute_names_route)
def model_component_edge_attribute_names(
    params: schemas.ModelComponentEdgeAttributeNames,
) -> schemas.ModelComponentEdgeAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeModel):
        flask.abort(400, f"{params.id} is not a GeodeModel")
    managers = [
        component.mesh().edge_attribute_manager()
        for component_id in params.component_ids
        if isinstance(
            (component := geode_object.component(og.uuid(component_id))),
            ComponentLine,
        )
    ]
    return schemas.ModelComponentEdgeAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(managers)}
    )


@typed_route(routes, schemas.model_component_polygon_attribute_names_route)
def model_component_polygon_attribute_names(
    params: schemas.ModelComponentPolygonAttributeNames,
) -> schemas.ModelComponentPolygonAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeModel):
        flask.abort(400, f"{params.id} is not a GeodeModel")
    managers = [
        component.mesh().polygon_attribute_manager()
        for component_id in params.component_ids
        if isinstance(
            (component := geode_object.component(og.uuid(component_id))),
            ComponentSurface,
        )
    ]
    return schemas.ModelComponentPolygonAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(managers)}
    )


@typed_route(routes, schemas.model_component_polyhedron_attribute_names_route)
def model_component_polyhedron_attribute_names(
    params: schemas.ModelComponentPolyhedronAttributeNames,
) -> schemas.ModelComponentPolyhedronAttributeNamesResponse:
    geode_object = geode_functions.load_geode_object(params.id)
    if not isinstance(geode_object, GeodeModel):
        flask.abort(400, f"{params.id} is not a GeodeModel")
    managers = [
        component.mesh().polyhedron_attribute_manager()
        for component_id in params.component_ids
        if isinstance(
            (component := geode_object.component(og.uuid(component_id))),
            ComponentBlock,
        )
    ]
    return schemas.ModelComponentPolyhedronAttributeNamesResponse.from_dict(
        {"attributes": attributes_metadata(managers)}
    )


@typed_route(routes, schemas.ping_route)
def ping(_params: schemas.Ping) -> schemas.PingResponse:
    flask.current_app.config.update(LAST_PING_TIME=time.time())
    return schemas.PingResponse(message="Flask server is running")


@typed_route(routes, schemas.kill_route)
def kill(_params: schemas.Kill) -> schemas.KillResponse:
    logger.info("Manual server kill, shutting down...")
    utils_functions.teardown_request(flask.current_app)
    Timer(0.5, os._exit, [0]).start()
    return schemas.KillResponse(message="Flask server is dead")


@raw_route(routes, schemas.export_project_route)
def export_project() -> flask.Response:
    params = parse_params(schemas.export_project_route)

    project_folder: str = flask.current_app.config["DATA_FOLDER_PATH"]
    Path(project_folder).mkdir(parents=True, exist_ok=True)

    filename: str = werkzeug.utils.secure_filename(Path(params.filename).name)
    if not filename.lower().endswith(".vease"):
        flask.abort(400, "Requested filename must end with .vease")
    export_vease_path = Path(project_folder) / filename

    with get_session() as session:
        rows = session.query(Data.id, Data.native_file).all()

    with zipfile.ZipFile(export_vease_path, "w", compression=zipfile.ZIP_DEFLATED) as zip_file:
        database_root_path = Path(project_folder) / "project.db"
        if database_root_path.is_file():
            zip_file.write(database_root_path, "project.db")

        for data_id, _native_file in rows:
            base_dir = Path(project_folder) / data_id
            if base_dir.is_dir():
                for file_path in base_dir.rglob("*"):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(base_dir)
                        zip_file.write(file_path, Path(data_id) / relative_path)

        zip_file.writestr("snapshot.json", flask.json.dumps(params.snapshot))

    return utils_functions.send_file(project_folder, [str(export_vease_path)], filename)


def _uploaded_vease_file() -> FileStorage:
    if "file" not in flask.request.files:
        flask.abort(400, "No .vease file provided under 'file'")
    zip_file = flask.request.files["file"]
    if zip_file.filename is None:
        flask.abort(400, "Filename is required")
    filename = werkzeug.utils.secure_filename(Path(zip_file.filename).name)
    if not filename.lower().endswith(".vease"):
        flask.abort(400, "Uploaded file must be a .vease")
    return zip_file


def _reset_data_folder(data_folder_path: Path) -> None:
    # 423 Locked bypass : remove stopped requests
    connection.close_database()

    try:
        if data_folder_path.exists():
            for item in data_folder_path.iterdir():
                if item.is_dir() and not item.is_symlink():
                    shutil.rmtree(item)
                else:
                    item.unlink()
        else:
            data_folder_path.mkdir(parents=True, exist_ok=True)
    except PermissionError:
        flask.abort(423, "Project files are locked; cannot overwrite")


def _extract_vease(zip_archive: zipfile.ZipFile, project_folder: Path) -> None:
    for member in zip_archive.namelist():
        target = (project_folder / member).resolve()
        if not target.is_relative_to(project_folder):
            flask.abort(400, "Vease file contains unsafe paths")
    zip_archive.extractall(project_folder)


def _open_project_database(project_folder: Path) -> list[Data]:
    database_root_path = project_folder / "project.db"
    if not database_root_path.is_file():
        flask.abort(400, "Missing project.db at project root")

    connection.init_database(database_root_path, create_tables=False)

    try:
        with get_session() as session:
            return session.query(Data).all()
    except OperationalError:
        connection.init_database(database_root_path, create_tables=True)
        with get_session() as session:
            return session.query(Data).all()


def _regenerate_missing_viewables(rows: list[Data]) -> None:
    with get_session() as session:
        for data in rows:
            data_path = geode_functions.data_file_path(data.id)
            viewable_name = data.viewable_file
            if viewable_name:
                vpath = Path(geode_functions.data_file_path(data.id, viewable_name))
                viewable_dir = Path(data_path) / "viewable"
                has_components = viewable_dir.is_dir() and any(viewable_dir.iterdir())
                if vpath.is_file() and (data.viewer_object != "model" or has_components):
                    continue

            native_file = str(data.native_file or "")
            if not native_file:
                continue

            native_full = geode_functions.data_file_path(data.id, native_file)
            if not Path(native_full).is_file():
                continue

            geode_object = geode_functions.geode_object_from_string(data.geode_object).load(
                native_full
            )
            utils_functions.save_all_viewables_and_return_info(geode_object, data, data_path)
        session.commit()


def _read_snapshot(zip_archive: zipfile.ZipFile) -> dict[str, object]:
    try:
        raw = zip_archive.read("snapshot.json").decode("utf-8")
    except KeyError:
        return {}
    snapshot: dict[str, object] = flask.json.loads(raw)
    return snapshot


@raw_route(routes, schemas.import_project_route)
def import_project() -> flask.Response:
    zip_file = _uploaded_vease_file()
    data_folder_path = Path(flask.current_app.config["DATA_FOLDER_PATH"])
    _reset_data_folder(data_folder_path)

    zip_file.stream.seek(0)
    with zipfile.ZipFile(zip_file.stream) as zip_archive:
        project_folder = data_folder_path.resolve()
        _extract_vease(zip_archive, project_folder)
        rows = _open_project_database(project_folder)
        _regenerate_missing_viewables(rows)
        snapshot = _read_snapshot(zip_archive)
    return flask.make_response(schemas.ImportProjectResponse(snapshot=snapshot).to_dict(), 200)


@typed_route(routes, schemas.geode_object_inheritance_route)
def geode_object_inheritance(
    params: schemas.GeodeObjectInheritance,
) -> schemas.GeodeObjectInheritanceResponse:
    geode_object_type = params.geode_object_type
    target_class = geode_functions.geode_object_from_string(geode_object_type)

    def get_all_bases(geode_class: type) -> set[type]:
        bases = set()
        for base_class in geode_class.__bases__:
            if base_class is not object:
                bases.add(base_class)
                bases.update(get_all_bases(base_class))
        return bases

    def get_all_subclasses(geode_class: type) -> set[type]:
        subclasses: set[type] = set()
        subclass_class: type
        for subclass_class in geode_class.__subclasses__():
            subclasses.add(subclass_class)
            subclasses.update(get_all_subclasses(subclass_class))
        return subclasses

    # Extract all related Geode classes (parents and children)
    base_classes = get_all_bases(target_class)
    subclass_classes = get_all_subclasses(target_class)

    # Filter GeodeObjectType to only include registered related objects, excluding target
    parents: list[str] = []
    children: list[str] = []
    for geode_object_type_str, geode_class in geode_objects.items():
        if geode_class == target_class:
            continue
        if geode_class in base_classes:
            parents.append(geode_object_type_str)
        if geode_class in subclass_classes:
            children.append(geode_object_type_str)

    return schemas.GeodeObjectInheritanceResponse(parents=parents, children=children)

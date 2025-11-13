# Standard library imports
import os
import time
import shutil

# Third party imports
import flask
import werkzeug
import zipfile
from opengeodeweb_microservice.schemas import get_schemas_dict

# Local application imports
from opengeodeweb_back import geode_functions, utils_functions
from .models import blueprint_models
from . import schemas
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_microservice.database import connection

routes = flask.Blueprint("routes", __name__, url_prefix="/opengeodeweb_back")


routes.register_blueprint(
    blueprint_models.routes,
    url_prefix=blueprint_models.routes.url_prefix,
    name=blueprint_models.routes.name,
)

schemas_dict = get_schemas_dict(os.path.join(os.path.dirname(__file__), "schemas"))


@routes.route(
    schemas_dict["allowed_files"]["route"],
    methods=schemas_dict["allowed_files"]["methods"],
)
def allowed_files() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["allowed_files"])
    params = schemas.AllowedFiles.from_dict(flask.request.get_json())
    extensions = geode_functions.list_input_extensions(params.supported_feature)
    return flask.make_response({"extensions": extensions}, 200)


@routes.route(
    schemas_dict["upload_file"]["route"],
    methods=schemas_dict["upload_file"]["methods"],
)
def upload_file() -> flask.Response:
    if flask.request.method == "OPTIONS":
        return flask.make_response({}, 200)

    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)

    file = flask.request.files["file"]
    filename = werkzeug.utils.secure_filename(os.path.basename(file.filename))
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return flask.make_response({"message": "File uploaded"}, 201)


@routes.route(
    schemas_dict["allowed_objects"]["route"],
    methods=schemas_dict["allowed_objects"]["methods"],
)
def allowed_objects() -> flask.Response:
    if flask.request.method == "OPTIONS":
        return flask.make_response({}, 200)

    utils_functions.validate_request(flask.request, schemas_dict["allowed_objects"])
    params = schemas.AllowedObjects.from_dict(flask.request.get_json())
    file_absolute_path = geode_functions.upload_file_path(params.filename)
    allowed_objects = geode_functions.list_geode_objects(
        file_absolute_path, params.supported_feature
    )
    return flask.make_response({"allowed_objects": allowed_objects}, 200)


@routes.route(
    schemas_dict["missing_files"]["route"],
    methods=schemas_dict["missing_files"]["methods"],
)
def missing_files() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["missing_files"])
    params = schemas.MissingFiles.from_dict(flask.request.get_json())
    file_path = geode_functions.upload_file_path(params.filename)

    additional_files = geode_functions.additional_files(
        params.input_geode_object,
        file_path,
    )

    has_missing_files = any(
        file.is_missing
        for file in additional_files.mandatory_files + additional_files.optional_files
    )

    mandatory_files = [
        os.path.basename(file.filename)
        for file in additional_files.mandatory_files
        if file.is_missing
    ]
    additional_files = [
        os.path.basename(file.filename)
        for file in additional_files.optional_files
        if file.is_missing
    ]

    return flask.make_response(
        {
            "has_missing_files": has_missing_files,
            "mandatory_files": mandatory_files,
            "additional_files": additional_files,
        },
        200,
    )


@routes.route(
    schemas_dict["geographic_coordinate_systems"]["route"],
    methods=schemas_dict["geographic_coordinate_systems"]["methods"],
)
def crs_converter_geographic_coordinate_systems() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["geographic_coordinate_systems"]
    )
    params = schemas.GeographicCoordinateSystems.from_dict(flask.request.get_json())
    infos = geode_functions.geographic_coordinate_systems(params.input_geode_object)
    crs_list = []
    for info in infos:
        crs = {}
        crs["name"] = info.name
        crs["code"] = info.code
        crs["authority"] = info.authority
        crs_list.append(crs)

    return flask.make_response({"crs_list": crs_list}, 200)


@routes.route(
    schemas_dict["inspect_file"]["route"],
    methods=schemas_dict["inspect_file"]["methods"],
)
def inspect_file() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["inspect_file"])
    params = schemas.InspectFile.from_dict(flask.request.get_json())
    file_path = geode_functions.upload_file_path(params.filename)
    data = geode_functions.load(params.input_geode_object, file_path)
    class_inspector = geode_functions.inspect(params.input_geode_object, data)
    inspection_result = geode_functions.get_inspector_children(class_inspector)
    return flask.make_response({"inspection_result": inspection_result}, 200)


@routes.route(
    schemas_dict["geode_objects_and_output_extensions"]["route"],
    methods=schemas_dict["geode_objects_and_output_extensions"]["methods"],
)
def geode_objects_and_output_extensions() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["geode_objects_and_output_extensions"]
    )
    params = schemas.GeodeObjectsAndOutputExtensions.from_dict(flask.request.get_json())
    file_path = geode_functions.upload_file_path(params.filename)
    data = geode_functions.load(
        params.input_geode_object,
        file_path,
    )
    geode_objects_and_output_extensions = (
        geode_functions.geode_objects_output_extensions(params.input_geode_object, data)
    )
    return flask.make_response(
        {"geode_objects_and_output_extensions": geode_objects_and_output_extensions},
        200,
    )


@routes.route(
    schemas_dict["save_viewable_file"]["route"],
    methods=schemas_dict["save_viewable_file"]["methods"],
)
def save_viewable_file() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["save_viewable_file"])
    params = schemas.SaveViewableFile.from_dict(flask.request.get_json())
    return flask.make_response(
        utils_functions.generate_native_viewable_and_light_viewable_from_file(
            geode_object=params.input_geode_object,
            input_filename=params.filename,
        ),
        200,
    )


@routes.route(
    schemas_dict["texture_coordinates"]["route"],
    methods=schemas_dict["texture_coordinates"]["methods"],
)
def texture_coordinates() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["texture_coordinates"])
    params = schemas.TextureCoordinates.from_dict(flask.request.get_json())
    data = geode_functions.load_data(params.id)
    texture_coordinates = data.texture_manager().texture_names()
    return flask.make_response({"texture_coordinates": texture_coordinates}, 200)


@routes.route(
    schemas_dict["vertex_attribute_names"]["route"],
    methods=schemas_dict["vertex_attribute_names"]["methods"],
)
def vertex_attribute_names() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["vertex_attribute_names"]
    )
    params = schemas.VertexAttributeNames.from_dict(flask.request.get_json())
    data = geode_functions.load_data(params.id)
    vertex_attribute_names = data.vertex_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "vertex_attribute_names": vertex_attribute_names,
        },
        200,
    )


@routes.route(
    schemas_dict["polygon_attribute_names"]["route"],
    methods=schemas_dict["polygon_attribute_names"]["methods"],
)
def polygon_attribute_names() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["polygon_attribute_names"]
    )
    params = schemas.PolygonAttributeNames.from_dict(flask.request.get_json())
    data = geode_functions.load_data(params.id)
    polygon_attribute_names = data.polygon_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "polygon_attribute_names": polygon_attribute_names,
        },
        200,
    )


@routes.route(
    schemas_dict["polyhedron_attribute_names"]["route"],
    methods=schemas_dict["polyhedron_attribute_names"]["methods"],
)
def polyhedron_attribute_names() -> flask.Response:
    utils_functions.validate_request(
        flask.request, schemas_dict["polyhedron_attribute_names"]
    )
    params = schemas.PolyhedronAttributeNames.from_dict(flask.request.get_json())
    data = geode_functions.load_data(params.id)
    polyhedron_attribute_names = data.polyhedron_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "polyhedron_attribute_names": polyhedron_attribute_names,
        },
        200,
    )


@routes.route(
    schemas_dict["ping"]["route"],
    methods=schemas_dict["ping"]["methods"],
)
def ping() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["ping"])
    flask.current_app.config.update(LAST_PING_TIME=time.time())
    return flask.make_response({"message": "Flask server is running"}, 200)


@routes.route(schemas_dict["kill"]["route"], methods=schemas_dict["kill"]["methods"])
def kill() -> flask.Response:
    print("Manual server kill, shutting down...", flush=True)
    os._exit(0)
    return flask.make_response({"message": "Flask server is dead"}, 200)


@routes.route(
    schemas_dict["export_project"]["route"],
    methods=schemas_dict["export_project"]["methods"],
)
def export_project() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["export_project"])
    params = schemas.ExportProject.from_dict(flask.request.get_json())

    project_folder: str = flask.current_app.config["DATA_FOLDER_PATH"]
    os.makedirs(project_folder, exist_ok=True)

    filename: str = werkzeug.utils.secure_filename(os.path.basename(params.filename))
    if not filename.lower().endswith(".vease"):
        flask.abort(400, "Requested filename must end with .vease")
    export_vease_path = os.path.join(project_folder, filename)

    with get_session() as session:
        rows = session.query(Data.id, Data.input_file, Data.additional_files).all()

    with zipfile.ZipFile(
        export_vease_path, "w", compression=zipfile.ZIP_DEFLATED
    ) as zip_file:
        database_root_path = os.path.join(project_folder, "project.db")
        if os.path.isfile(database_root_path):
            zip_file.write(database_root_path, "project.db")

        for data_id, input_file, additional_files in rows:
            base_dir = os.path.join(project_folder, data_id)

            input_path = os.path.join(base_dir, str(input_file))
            if os.path.isfile(input_path):
                zip_file.write(input_path, os.path.join(data_id, str(input_file)))

            for relative_path in (
                additional_files if isinstance(additional_files, list) else []
            ):
                additional_path = os.path.join(base_dir, relative_path)
                if os.path.isfile(additional_path):
                    zip_file.write(
                        additional_path, os.path.join(data_id, relative_path)
                    )

        zip_file.writestr("snapshot.json", flask.json.dumps(params.snapshot))

    return utils_functions.send_file(project_folder, [export_vease_path], filename)


@routes.route(
    schemas_dict["import_project"]["route"],
    methods=schemas_dict["import_project"]["methods"],
)
def import_project() -> flask.Response:
    utils_functions.validate_request(flask.request, schemas_dict["import_project"])
    if "file" not in flask.request.files:
        flask.abort(400, "No .vease file provided under 'file'")
    zip_file = flask.request.files["file"]
    assert zip_file.filename is not None
    filename = werkzeug.utils.secure_filename(os.path.basename(zip_file.filename))
    if not filename.lower().endswith(".vease"):
        flask.abort(400, "Uploaded file must be a .vease")

    data_folder_path: str = flask.current_app.config["DATA_FOLDER_PATH"]

    # 423 Locked bypass : remove stopped requests
    if connection.scoped_session_registry:
        connection.scoped_session_registry.remove()
    if connection.engine:
        connection.engine.dispose()
    connection.engine = connection.session_factory = (
        connection.scoped_session_registry
    ) = None

    try:
        if os.path.exists(data_folder_path):
            shutil.rmtree(data_folder_path)
        os.makedirs(data_folder_path, exist_ok=True)
    except PermissionError:
        flask.abort(423, "Project files are locked; cannot overwrite")

    zip_file.stream.seek(0)
    with zipfile.ZipFile(zip_file.stream) as zip_archive:
        project_folder = os.path.abspath(data_folder_path)
        for member in zip_archive.namelist():
            target = os.path.abspath(
                os.path.normpath(os.path.join(project_folder, member))
            )
            if not (
                target == project_folder or target.startswith(project_folder + os.sep)
            ):
                flask.abort(400, "Vease file contains unsafe paths")
        zip_archive.extractall(project_folder)

        database_root_path = os.path.join(project_folder, "project.db")
        if not os.path.isfile(database_root_path):
            flask.abort(400, "Missing project.db at project root")

        connection.init_database(database_root_path, create_tables=False)

        try:
            with get_session() as session:
                rows = session.query(Data).all()
        except Exception:
            connection.init_database(database_root_path, create_tables=True)
            with get_session() as session:
                rows = session.query(Data).all()

        with get_session() as session:
            for data_entry in rows:
                data_path = geode_functions.data_file_path(data_entry.id)
                viewable_name = data_entry.viewable_file_name
                if viewable_name:
                    vpath = geode_functions.data_file_path(data_entry.id, viewable_name)
                    if os.path.isfile(vpath):
                        continue

                input_file = str(data_entry.input_file or "")
                if not input_file:
                    continue

                input_full = geode_functions.data_file_path(data_entry.id, input_file)
                if not os.path.isfile(input_full):
                    continue

                data_object = geode_functions.load(data_entry.geode_object, input_full)
                utils_functions.save_all_viewables_and_return_info(
                    data_entry.geode_object, data_object, data_entry, data_path
                )
            session.commit()

        snapshot = {}
        try:
            raw = zip_archive.read("snapshot.json").decode("utf-8")
            snapshot = flask.json.loads(raw)
        except KeyError:
            snapshot = {}
    return flask.make_response({"snapshot": snapshot}, 200)

# Standard library imports
import json
import os
import time

# Third party imports
import flask
import opengeode
import werkzeug

# Local application imports
from .. import geode_functions, utils_functions

from .models import blueprint_models

routes = flask.Blueprint("routes", __name__, url_prefix="/opengeodeweb_back")


@routes.before_request
def before_request():
    if "ping" not in flask.request.path:
        utils_functions.increment_request_counter(flask.current_app)


@routes.teardown_request
def teardown_request(exception):

    if "ping" not in flask.request.path:
        utils_functions.decrement_request_counter(flask.current_app)
        utils_functions.update_last_request_time(flask.current_app)


routes.register_blueprint(
    blueprint_models.routes,
    url_prefix=blueprint_models.routes.url_prefix,
    name=blueprint_models.routes.name,
)


schemas = os.path.join(os.path.dirname(__file__), "schemas")

with open(
    os.path.join(schemas, "allowed_files.json"),
    "r",
) as file:
    allowed_files_json = json.load(file)


@routes.route(
    allowed_files_json["route"],
    methods=allowed_files_json["methods"],
)
def allowed_files():
    utils_functions.validate_request(flask.request, allowed_files_json)
    extensions = geode_functions.list_input_extensions(
        flask.request.get_json()["supported_feature"]
    )
    return flask.make_response({"extensions": extensions}, 200)


with open(
    os.path.join(schemas, "upload_file.json"),
    "r",
) as file:
    upload_file_json = json.load(file)


@routes.route(
    upload_file_json["route"],
    methods=upload_file_json["methods"],
)
def upload_file():
    if flask.request.method == "OPTIONS":
        return flask.make_response({}, 200)

    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    if not os.path.exists(UPLOAD_FOLDER):
        os.mkdir(UPLOAD_FOLDER)
    file = flask.request.files["file"]
    filename = werkzeug.utils.secure_filename(os.path.basename(file.filename))
    file.save(os.path.join(UPLOAD_FOLDER, filename))
    return flask.make_response({"message": "File uploaded"}, 201)


with open(
    os.path.join(schemas, "allowed_objects.json"),
    "r",
) as file:
    allowed_objects_json = json.load(file)


@routes.route(
    allowed_objects_json["route"],
    methods=allowed_objects_json["methods"],
)
def allowed_objects():
    if flask.request.method == "OPTIONS":
        return flask.make_response({}, 200)

    utils_functions.validate_request(flask.request, allowed_objects_json)
    file_absolute_path = geode_functions.upload_file_path(
        flask.request.get_json()["filename"]
    )
    allowed_objects = geode_functions.list_geode_objects(
        file_absolute_path, flask.request.get_json()["supported_feature"]
    )
    return flask.make_response({"allowed_objects": allowed_objects}, 200)


with open(
    os.path.join(schemas, "missing_files.json"),
    "r",
) as file:
    missing_files_json = json.load(file)


@routes.route(
    missing_files_json["route"],
    methods=missing_files_json["methods"],
)
def missing_files():
    utils_functions.validate_request(flask.request, missing_files_json)
    file_path = geode_functions.upload_file_path(flask.request.get_json()["filename"])

    additional_files = geode_functions.additional_files(
        flask.request.get_json()["input_geode_object"],
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


with open(
    os.path.join(schemas, "geographic_coordinate_systems.json"),
    "r",
) as file:
    geographic_coordinate_systems_json = json.load(file)


@routes.route(
    geographic_coordinate_systems_json["route"],
    methods=geographic_coordinate_systems_json["methods"],
)
def crs_converter_geographic_coordinate_systems():
    utils_functions.validate_request(flask.request, geographic_coordinate_systems_json)
    infos = geode_functions.geographic_coordinate_systems(
        flask.request.get_json()["input_geode_object"]
    )
    crs_list = []
    for info in infos:
        crs = {}
        crs["name"] = info.name
        crs["code"] = info.code
        crs["authority"] = info.authority
        crs_list.append(crs)

    return flask.make_response({"crs_list": crs_list}, 200)


with open(
    os.path.join(schemas, "inspect_file.json"),
    "r",
) as file:
    inspect_file_json = json.load(file)


@routes.route(
    inspect_file_json["route"],
    methods=inspect_file_json["methods"],
)
def inspect_file():
    utils_functions.validate_request(flask.request, inspect_file_json)

    file_path = geode_functions.upload_file_path(flask.request.get_json()["filename"])
    data = geode_functions.load(
        flask.request.get_json()["input_geode_object"], file_path
    )
    class_inspector = geode_functions.inspect(
        flask.request.get_json()["input_geode_object"], data
    )
    inspection_result = geode_functions.get_inspector_children(class_inspector)
    return flask.make_response({"inspection_result": inspection_result}, 200)


with open(
    os.path.join(schemas, "geode_objects_and_output_extensions.json"),
    "r",
) as file:
    geode_objects_and_output_extensions_json = json.load(file)


@routes.route(
    geode_objects_and_output_extensions_json["route"],
    methods=geode_objects_and_output_extensions_json["methods"],
)
def geode_objects_and_output_extensions():
    utils_functions.validate_request(
        flask.request, geode_objects_and_output_extensions_json
    )
    file_path = geode_functions.upload_file_path(flask.request.get_json()["filename"])
    data = geode_functions.load(
        flask.request.get_json()["input_geode_object"],
        file_path,
    )
    geode_objects_and_output_extensions = (
        geode_functions.geode_objects_output_extensions(
            flask.request.get_json()["input_geode_object"], data
        )
    )
    return flask.make_response(
        {"geode_objects_and_output_extensions": geode_objects_and_output_extensions},
        200,
    )


with open(
    os.path.join(schemas, "save_viewable_file.json"),
    "r",
) as file:
    save_viewable_file_json = json.load(file)


@routes.route(
    save_viewable_file_json["route"],
    methods=save_viewable_file_json["methods"],
)
def save_viewable_file():
    utils_functions.validate_request(flask.request, save_viewable_file_json)
    return flask.make_response(
        utils_functions.generate_native_viewable_and_light_viewable_from_file(
            geode_object=flask.request.get_json()["input_geode_object"],
            input_filename=flask.request.get_json()["filename"],
        ),
        200,
    )


with open(os.path.join(schemas, "create_point.json"), "r") as file:
    create_point_json = json.load(file)


@routes.route(create_point_json["route"], methods=create_point_json["methods"])
def create_point():
    utils_functions.validate_request(flask.request, create_point_json)
    title = flask.request.get_json()["title"]
    x = flask.request.get_json()["x"]
    y = flask.request.get_json()["y"]
    z = flask.request.get_json()["z"]
    class_ = geode_functions.geode_object_class("PointSet3D")
    PointSet3D = class_.create()
    builder = geode_functions.create_builder("PointSet3D", PointSet3D)
    builder.create_point(opengeode.Point3D([x, y, z]))
    builder.set_name(title)
    return flask.make_response(
        utils_functions.generate_native_viewable_and_light_viewable_from_object(
            "PointSet3D", PointSet3D
        ),
        200,
    )


with open(os.path.join(schemas, "texture_coordinates.json"), "r") as file:
    texture_coordinates_json = json.load(file)


@routes.route(
    texture_coordinates_json["route"],
    methods=texture_coordinates_json["methods"],
)
def texture_coordinates():
    utils_functions.validate_request(flask.request, texture_coordinates_json)
    data = geode_functions.load_data(flask.request.get_json().get("id"))
    texture_coordinates = data.texture_manager().texture_names()
    return flask.make_response({"texture_coordinates": texture_coordinates}, 200)


with open(
    os.path.join(schemas, "vertex_attribute_names.json"),
    "r",
) as file:
    vertex_attribute_names_json = json.load(file)


@routes.route(
    vertex_attribute_names_json["route"],
    methods=vertex_attribute_names_json["methods"],
)
def vertex_attribute_names():
    utils_functions.validate_request(flask.request, vertex_attribute_names_json)
    data = geode_functions.load_data(flask.request.get_json().get("id"))
    vertex_attribute_names = data.vertex_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "vertex_attribute_names": vertex_attribute_names,
        },
        200,
    )


with open(
    os.path.join(schemas, "polygon_attribute_names.json"),
    "r",
) as file:
    polygon_attribute_names_json = json.load(file)


@routes.route(
    polygon_attribute_names_json["route"],
    methods=polygon_attribute_names_json["methods"],
)
def polygon_attribute_names():
    utils_functions.validate_request(flask.request, polygon_attribute_names_json)
    data = geode_functions.load_data(flask.request.get_json().get("id"))
    polygon_attribute_names = data.polygon_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "polygon_attribute_names": polygon_attribute_names,
        },
        200,
    )


with open(
    os.path.join(schemas, "polyhedron_attribute_names.json"),
    "r",
) as file:
    polyhedron_attribute_names_json = json.load(file)


@routes.route(
    polyhedron_attribute_names_json["route"],
    methods=polyhedron_attribute_names_json["methods"],
)
def polyhedron_attribute_names():
    utils_functions.validate_request(flask.request, polyhedron_attribute_names_json)
    data = geode_functions.load_data(flask.request.get_json().get("id"))
    polyhedron_attribute_names = data.polyhedron_attribute_manager().attribute_names()
    return flask.make_response(
        {
            "polyhedron_attribute_names": polyhedron_attribute_names,
        },
        200,
    )


with open(
    os.path.join(schemas, "ping.json"),
    "r",
) as file:
    ping_json = json.load(file)


@routes.route(
    ping_json["route"],
    methods=ping_json["methods"],
)
def ping():
    utils_functions.validate_request(flask.request, ping_json)
    flask.current_app.config.update(LAST_PING_TIME=time.time())
    return flask.make_response({"message": "Flask server is running"}, 200)

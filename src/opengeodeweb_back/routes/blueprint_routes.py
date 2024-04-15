# Standard library imports
import json
import os

# Third party imports
import flask
import flask_cors
from .. import geode_functions
import werkzeug


routes = flask.Blueprint("routes", __name__)
flask_cors.CORS(routes)


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
    geode_functions.validate_request(flask.request, allowed_files_json)
    extensions = geode_functions.list_input_extensions(
        flask.request.json["supported_feature"]
    )
    return {"status": 200, "extensions": extensions}


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

    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    geode_functions.validate_request(flask.request, allowed_objects_json)
    file_absolute_path = os.path.join(UPLOAD_FOLDER, flask.request.json["filename"])
    allowed_objects = geode_functions.list_geode_objects(
        file_absolute_path, flask.request.json["supported_feature"]
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
    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    geode_functions.validate_request(flask.request, missing_files_json)

    missing_files = geode_functions.missing_files(
        flask.request.json["input_geode_object"],
        os.path.join(UPLOAD_FOLDER, flask.request.json["filename"]),
    )
    has_missing_files = missing_files.has_missing_files()

    mandatory_files = []
    for mandatory_file in missing_files.mandatory_files:
        mandatory_files.append(os.path.basename(mandatory_file))

    additional_files = []
    for additional_file in missing_files.additional_files:
        additional_files.append(os.path.basename(additional_file))

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
    geode_functions.validate_request(flask.request, geographic_coordinate_systems_json)
    infos = geode_functions.geographic_coordinate_systems(
        flask.request.json["input_geode_object"]
    )
    crs_list = []
    print(infos)
    print(flask.request.json["input_geode_object"])
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


def get_inspector_children(obj):
    array = []
    print(f"{obj=}", flush=True)

    if "inspection_type" in dir(obj):
        new_object = {"title": obj.inspection_type()}
        print(f"{obj.inspection_type()=}", flush=True)
        for obj_child in dir(obj):
            if not obj_child.startswith('__') and not obj_child in ["inspection_type"] and type(obj.__getattribute__(obj_child)).__name__ != 'builtin_function_or_method':
                print(f"{obj_child=}", flush=True)
                child_instance = obj.__getattribute__(obj_child)
                print(f"{child_instance=}", flush=True)
                if child_instance != {}:
                    class_children = get_inspector_children(child_instance)
                    if class_children != []:
                        new_object["children"] = class_children
    else:
        print(f"ELSE {obj=} {dir(obj)=}", flush=True)
        new_object = {"title": ""}
        nb_issues = obj.nb_issues()
        issues = obj.issues()

        print(f"{nb_issues=}{issues=}", flush=True)
        
    array.append(new_object)
    return array

@routes.route(
    inspect_file_json["route"],
    methods=inspect_file_json["methods"],
)
def inspect_file():
    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    geode_functions.validate_request(flask.request, inspect_file_json)

    secure_filename = werkzeug.utils.secure_filename(flask.request.json["filename"])
    file_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, secure_filename))
    data = geode_functions.load(flask.request.json["input_geode_object"], file_path)
    inspector = geode_functions.inspector(
        flask.request.json["input_geode_object"], data
    )

    inspection_result = geode_functions.inspect(flask.request.json["input_geode_object"], inspector)
    print(f"{inspection_result=}", flush=True)

    tree = get_inspector_children(inspection_result)
    print(f"{tree=}", flush=True)


    return flask.make_response({"tree": tree}, 200)


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
    UPLOAD_FOLDER = flask.current_app.config["UPLOAD_FOLDER"]
    geode_functions.validate_request(
        flask.request, geode_objects_and_output_extensions_json
    )
    data = geode_functions.load(
        flask.request.json["input_geode_object"],
        os.path.join(UPLOAD_FOLDER, flask.request.json["filename"]),
    )
    geode_objects_and_output_extensions = (
        geode_functions.geode_objects_output_extensions(
            flask.request.json["input_geode_object"], data
        )
    )
    return flask.make_response(
        {"geode_objects_and_output_extensions": geode_objects_and_output_extensions},
        200,
    )

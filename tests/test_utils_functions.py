# Standard library imports
import re
import os

# Third party imports
import flask
import shutil
import uuid
import zipfile
import io

# Local application imports
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_microservice.database.connection import get_session
from opengeodeweb_back import geode_functions, utils_functions

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_increment_request_counter(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.increment_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_decrement_request_counter(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.decrement_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0


def test_update_last_request_time(app_context):
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    utils_functions.update_last_request_time(flask.current_app)
    assert flask.current_app.config.get("LAST_REQUEST_TIME") >= LAST_REQUEST_TIME


def test_before_request(app_context):
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.before_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_teardown_request(app_context):
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.teardown_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    assert flask.current_app.config.get("LAST_REQUEST_TIME") >= LAST_REQUEST_TIME


def test_versions():
    list_packages = [
        "OpenGeode-core",
        "OpenGeode-IO",
        "OpenGeode-Geosciences",
        "OpenGeode-GeosciencesIO",
    ]
    versions = utils_functions.versions(list_packages)
    assert type(versions) is list
    for version in versions:
        assert type(version) is dict


def test_extension_from_filename():
    extension = utils_functions.extension_from_filename("test.toto")
    assert type(extension) is str
    assert extension.count(".") == 0


def test_handle_exception(client):
    route = "/error"
    response = client.post(route)
    assert response.status_code == 500
    data = response.get_json()
    assert type(data) is dict
    assert type(data["description"]) is str
    assert type(data["name"]) is str
    assert type(data["code"]) is int


def test_create_data_folder_from_id(client):
    app = client.application
    with app.app_context():
        test_id = str(uuid.uuid4()).replace("-", "")
        data_path = utils_functions.create_data_folder_from_id(test_id)
        assert isinstance(data_path, str)
        assert os.path.exists(data_path)
        assert data_path.startswith(flask.current_app.config["DATA_FOLDER_PATH"])
        assert test_id in data_path
        shutil.rmtree(data_path, ignore_errors=True)
        assert not os.path.exists(data_path)


def test_save_all_viewables_and_return_info(client):
    app = client.application
    with app.app_context():
        expected_db_path = os.path.join(data_dir, "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri
        assert os.path.exists(expected_db_path)

        geode_object = "BRep"
        data = geode_functions.load(
            geode_object, os.path.join(data_dir, "test.og_brep")
        )
        input_file = "test.og_brep"
        additional_files = ["additional_file.txt"]

        data_entry = Data.create(
            geode_object=geode_object,
            viewer_object=geode_functions.get_object_type(geode_object),
            input_file=input_file,
            additional_files=additional_files,
        )
        data_path = utils_functions.create_data_folder_from_id(data_entry.id)

        result = utils_functions.save_all_viewables_and_return_info(
            geode_object, data, data_entry, data_path
        )

        assert isinstance(result, dict)
        assert result["native_file_name"].startswith("native.")
        assert result["viewable_file_name"].endswith(".vtm")
        assert isinstance(result["id"], str)
        assert len(result["id"]) == 32
        assert re.match(r"[0-9a-f]{32}", result["id"])
        assert isinstance(result["object_type"], str)
        assert isinstance(result["binary_light_viewable"], str)
        assert result["geode_object"] == geode_object
        assert result["input_file"] == input_file

        db_entry = Data.get(result["id"])
        assert db_entry is not None
        assert db_entry.native_file_name == result["native_file_name"]
        assert db_entry.viewable_file_name == result["viewable_file_name"]
        assert db_entry.geode_object == geode_object
        assert db_entry.input_file == input_file
        assert db_entry.additional_files == additional_files

        expected_data_path = os.path.join(app.config["DATA_FOLDER_PATH"], result["id"])
        assert os.path.exists(expected_data_path)


def test_save_all_viewables_commits_to_db(client):
    app = client.application
    with app.app_context():
        geode_object = "BRep"
        data = geode_functions.load(
            geode_object, os.path.join(data_dir, "test.og_brep")
        )
        input_file = "test.og_brep"

        data_entry = Data.create(
            geode_object=geode_object,
            viewer_object=geode_functions.get_object_type(geode_object),
            input_file=input_file,
            additional_files=[],
        )
        data_path = utils_functions.create_data_folder_from_id(data_entry.id)

        result = utils_functions.save_all_viewables_and_return_info(
            geode_object, data, data_entry, data_path
        )
        data_id = result["id"]
        db_entry_before = Data.get(data_id)
        assert db_entry_before is not None
        assert db_entry_before.native_file_name == result["native_file_name"]


def test_generate_native_viewable_and_light_viewable_from_object(client):
    app = client.application
    with app.app_context():
        geode_object = "BRep"
        data = geode_functions.load(
            geode_object, os.path.join(data_dir, "test.og_brep")
        )

        result = (
            utils_functions.generate_native_viewable_and_light_viewable_from_object(
                geode_object, data
            )
        )

    assert isinstance(result, dict)
    assert isinstance(result["native_file_name"], str)
    assert result["native_file_name"].startswith("native.")
    assert isinstance(result["viewable_file_name"], str)
    assert result["viewable_file_name"].endswith(".vtm")
    assert isinstance(result["id"], str)
    assert re.match(r"[0-9a-f]{32}", result["id"])
    assert isinstance(result["object_type"], str)
    assert isinstance(result["binary_light_viewable"], str)
    assert result["input_file"] == None


def test_generate_native_viewable_and_light_viewable_from_file(client):
    app = client.application
    with app.app_context():
        geode_object = "BRep"
        input_filename = "test.og_brep"

        result = utils_functions.generate_native_viewable_and_light_viewable_from_file(
            geode_object, input_filename
        )

    assert isinstance(result, dict)
    assert isinstance(result["native_file_name"], str)
    assert result["native_file_name"].startswith("native.")
    assert isinstance(result["viewable_file_name"], str)
    assert result["viewable_file_name"].endswith(".vtm")
    assert isinstance(result["id"], str)
    assert re.match(r"[0-9a-f]{32}", result["id"])
    assert isinstance(result["object_type"], str)
    assert isinstance(result["binary_light_viewable"], str)
    assert isinstance(result["input_file"], str)


def test_send_file_multiple_returns_zip(client, tmp_path):
    app = client.application
    with app.app_context():
        app.config["UPLOAD_FOLDER"] = str(tmp_path)
        file_paths = []
        for i, content in [(1, b"hello 1"), (2, b"hello 2")]:
            file_path = tmp_path / f"tmp_send_file_{i}.txt"
            file_path.write_bytes(content)
            file_paths.append(str(file_path))
        with app.test_request_context():
            response = utils_functions.send_file(
                app.config["UPLOAD_FOLDER"], file_paths, "bundle"
            )
            assert response.status_code == 200
            assert response.mimetype == "application/zip"
            new_file_name = response.headers.get("new-file-name")
            assert new_file_name == "bundle.zip"
            zip_path = os.path.join(app.config["UPLOAD_FOLDER"], new_file_name)
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                zip_entries = zip_file.namelist()
                assert "tmp_send_file_1.txt" in zip_entries
                assert "tmp_send_file_2.txt" in zip_entries
            response.close()


def test_send_file_single_returns_octet_binary(client, tmp_path):
    app = client.application
    with app.app_context():
        app.config["UPLOAD_FOLDER"] = str(tmp_path)
        file_path = tmp_path / "tmp_send_file_1.txt"
        file_path.write_bytes(b"hello 1")
        with app.test_request_context():
            response = utils_functions.send_file(
                app.config["UPLOAD_FOLDER"], [str(file_path)], "tmp_send_file_1.txt"
            )
            assert response.status_code == 200
            assert response.mimetype == "application/octet-binary"
            new_file_name = response.headers.get("new-file-name")
            assert new_file_name == "tmp_send_file_1.txt"
            zip_path = os.path.join(app.config["UPLOAD_FOLDER"], new_file_name)
            with open(zip_path, "rb") as f:
                file_bytes = f.read()
            assert file_bytes == b"hello 1"
            response.close()

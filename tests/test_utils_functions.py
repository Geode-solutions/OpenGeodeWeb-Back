# Standard library imports
import re
import os

# Third party imports
import flask
from flask.ctx import AppContext
from flask.testing import FlaskClient
import shutil
import uuid
import zipfile
from pathlib import Path

# Local application imports
from opengeodeweb_microservice.database.data import Data
from opengeodeweb_back import utils_functions
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep

base_dir = os.path.abspath(os.path.dirname(__file__))
data_dir = os.path.join(base_dir, "data")


def test_increment_request_counter(app_context: AppContext) -> None:
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.increment_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_decrement_request_counter(app_context: AppContext) -> None:
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.decrement_request_counter(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0


def test_update_last_request_time(app_context: AppContext) -> None:
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    utils_functions.update_last_request_time(flask.current_app)
    assert flask.current_app.config.get("LAST_REQUEST_TIME", 0) >= LAST_REQUEST_TIME


def test_before_request(app_context: AppContext) -> None:
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    utils_functions.before_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1


def test_teardown_request(app_context: AppContext) -> None:
    LAST_REQUEST_TIME = flask.current_app.config.get("LAST_REQUEST_TIME")
    assert flask.current_app.config.get("REQUEST_COUNTER") == 1
    utils_functions.teardown_request(flask.current_app)
    assert flask.current_app.config.get("REQUEST_COUNTER") == 0
    assert flask.current_app.config.get("LAST_REQUEST_TIME", 0) >= LAST_REQUEST_TIME


def test_versions() -> None:
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


def test_extension_from_filename() -> None:
    extension = utils_functions.extension_from_filename("test.toto")
    assert type(extension) is str
    assert extension.count(".") == 0


def test_handle_exception(client: FlaskClient) -> None:
    route = "/error"
    response = client.post(route)
    assert response.status_code == 500
    data = response.get_json()
    assert type(data) is dict
    assert type(data["description"]) is str
    assert type(data["name"]) is str
    assert type(data["code"]) is int


def test_create_data_folder_from_id(client: FlaskClient) -> None:
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


def test_save_all_viewables_and_return_info(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        expected_db_path = os.path.join(data_dir, "project.db")
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri
        assert os.path.exists(expected_db_path)

        geode_object = GeodeBRep.load(os.path.join(data_dir, "test.og_brep"))
        input_file = "test.og_brep"
        additional_files = ["additional_file.txt"]

        data_entry = Data.create(
            geode_object=geode_object.geode_object_type(),
            viewer_object=geode_object.viewer_type(),
            input_file=input_file,
            additional_files=additional_files,
        )
        data_path = utils_functions.create_data_folder_from_id(data_entry.id)

        result = utils_functions.save_all_viewables_and_return_info(
            geode_object, data_entry, data_path
        )

        assert isinstance(result, dict)
        native_file = result["native_file"]
        assert isinstance(native_file, str)
        assert native_file.startswith("native.")
        viewable_file = result["viewable_file"]
        assert isinstance(viewable_file, str)
        assert viewable_file.endswith(".vtm")
        assert isinstance(result["id"], str)
        assert len(result["id"]) == 32
        assert re.match(r"[0-9a-f]{32}", result["id"])
        assert isinstance(result["viewer_type"], str)
        assert isinstance(result["binary_light_viewable"], str)
        assert result["geode_object_type"] == geode_object.geode_object_type()
        assert result["input_file"] == input_file

        db_entry = Data.get(result["id"])
        assert db_entry is not None
        assert db_entry.native_file == result["native_file"]
        assert db_entry.viewable_file == result["viewable_file"]
        assert db_entry.geode_object == geode_object.geode_object_type()
        assert db_entry.input_file == input_file
        assert db_entry.additional_files == additional_files

        expected_data_path = os.path.join(app.config["DATA_FOLDER_PATH"], result["id"])
        assert os.path.exists(expected_data_path)


def test_save_all_viewables_commits_to_db(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        geode_object = GeodeBRep.load(os.path.join(data_dir, "test.og_brep"))
        input_file = "test.og_brep"
        data_entry = Data.create(
            geode_object=geode_object.geode_object_type(),
            viewer_object=geode_object.viewer_type(),
            input_file=input_file,
            additional_files=[],
        )
        data_path = utils_functions.create_data_folder_from_id(data_entry.id)

        result = utils_functions.save_all_viewables_and_return_info(
            geode_object, data_entry, data_path
        )
        data_id = result["id"]
        assert isinstance(data_id, str)
        db_entry_before = Data.get(data_id)
        assert db_entry_before is not None
        assert db_entry_before.native_file == result["native_file"]


def test_generate_native_viewable_and_light_viewable_from_object(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        geode_object = GeodeBRep.load(os.path.join(data_dir, "test.og_brep"))

        result = (
            utils_functions.generate_native_viewable_and_light_viewable_from_object(
                geode_object
            )
        )

        assert isinstance(result, dict)
        assert isinstance(result["native_file"], str)
        assert result["native_file"].startswith("native.")
        assert isinstance(result["viewable_file"], str)
        assert result["viewable_file"].endswith(".vtm")
        assert isinstance(result["id"], str)
        assert re.match(r"[0-9a-f]{32}", result["id"])
        assert isinstance(result["viewer_type"], str)
        assert isinstance(result["binary_light_viewable"], str)
        assert result["binary_light_viewable"].startswith('<?xml version="1.0"?>')

        assert result["input_file"] == result["native_file"]

        data = Data.get(result["id"])
        assert data is not None
        assert data.input_file == data.native_file
        assert data.light_viewable_file is not None
        assert data.light_viewable_file.endswith(".vtp")

        data_path = os.path.join(app.config["DATA_FOLDER_PATH"], result["id"])
        assert os.path.exists(os.path.join(data_path, result["native_file"]))
        assert os.path.exists(os.path.join(data_path, result["viewable_file"]))
        assert os.path.exists(os.path.join(data_path, data.light_viewable_file))


def test_generate_native_viewable_and_light_viewable_from_file(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        result = utils_functions.generate_native_viewable_and_light_viewable_from_file(
            GeodeBRep.geode_object_type(), "test.og_brep"
        )

    assert isinstance(result, dict)
    assert isinstance(result["native_file"], str)
    assert result["native_file"].startswith("native.")
    assert isinstance(result["viewable_file"], str)
    assert result["viewable_file"].endswith(".vtm")
    assert isinstance(result["id"], str)
    assert re.match(r"[0-9a-f]{32}", result["id"])
    assert isinstance(result["viewer_type"], str)
    assert isinstance(result["binary_light_viewable"], str)
    assert isinstance(result["input_file"], str)


def test_send_file_multiple_returns_zip(client: FlaskClient, tmp_path: Path) -> None:
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


def test_send_file_single_returns_octet_binary(
    client: FlaskClient, tmp_path: Path
) -> None:
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

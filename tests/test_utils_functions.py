# Standard library imports
import base64
import re

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
from opengeodeweb_back import geode_functions, utils_functions
from opengeodeweb_back.geode_objects.geode_brep import GeodeBRep
from opengeodeweb_back.geode_objects.geode_polygonal_surface3d import (
    GeodePolygonalSurface3D,
)

base_dir = Path(__file__).resolve().parent
data_dir = base_dir / "data"


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
        assert Path(data_path).exists()
        assert Path(data_path).is_relative_to(flask.current_app.config["DATA_FOLDER_PATH"])
        assert test_id in data_path
        shutil.rmtree(data_path, ignore_errors=True)
        assert not Path(data_path).exists()


def test_save_all_viewables_and_return_info(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        expected_db_path = (Path(app.config["DATA_FOLDER_PATH"]) / "project.db").resolve()
        expected_uri = f"sqlite:///{expected_db_path}"

        assert app.config["SQLALCHEMY_DATABASE_URI"] == expected_uri
        assert expected_db_path.exists()

        geode_object = GeodeBRep.load(str(data_dir / "test.og_brep"))

        data_entry = Data.create(
            geode_id=geode_object.identifier.id().string(),
            geode_object=geode_object.geode_object_type(),
            viewer_object=geode_object.viewer_type(),
            viewer_elements_type=geode_object.viewer_elements_type(),
        )
        data_path = utils_functions.create_data_folder_from_id(data_entry.id)

        result = utils_functions.save_all_viewables_and_return_info(
            geode_object, data_entry, data_path
        )

        assert isinstance(result, dict)
        native_file = result["native_file"]
        assert isinstance(native_file, str)
        assert native_file == "native.og_brep"
        viewable_file = result["viewable_file"]
        assert isinstance(viewable_file, str)
        assert viewable_file.endswith(".vtm")
        assert isinstance(result["id"], str)
        assert len(result["id"]) == 32
        assert re.match(r"[0-9a-f]{32}", result["id"])
        assert result["geode_id"] == geode_object.identifier.id().string()
        assert isinstance(result["viewer_type"], str)
        assert isinstance(result["binary_light_viewable"], str)
        assert result["geode_object_type"] == geode_object.geode_object_type()

        db_entry = Data.get(result["id"])
        assert db_entry is not None
        assert db_entry.native_file == result["native_file"]
        assert db_entry.viewable_file == result["viewable_file"]
        assert db_entry.geode_object == geode_object.geode_object_type()

        expected_data_path = Path(app.config["DATA_FOLDER_PATH"]) / result["id"]
        assert expected_data_path.exists()


def test_save_all_viewables_commits_to_db(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        geode_object = GeodeBRep.load(str(data_dir / "test.og_brep"))
        data_entry = Data.create(
            geode_id=geode_object.identifier.id().string(),
            geode_object=geode_object.geode_object_type(),
            viewer_object=geode_object.viewer_type(),
            viewer_elements_type=geode_object.viewer_elements_type(),
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


def test_generate_files_from_object(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        geode_object = GeodeBRep.load(str(data_dir / "test.og_brep"))

        result = utils_functions.generate_files_from_object(geode_object)

        assert isinstance(result, dict)
        assert isinstance(result["native_file"], str)
        assert result["native_file"].startswith("native.")
        assert isinstance(result["viewable_file"], str)
        assert result["viewable_file"].endswith(".vtm")
        assert isinstance(result["id"], str)
        assert re.match(r"[0-9a-f]{32}", result["id"])
        assert isinstance(result["viewer_type"], str)
        assert isinstance(result["binary_light_viewable"], str)
        light_viewable_bytes = base64.b64decode(result["binary_light_viewable"], validate=True)
        assert light_viewable_bytes.startswith(b'<?xml version="1.0"?>')
        assert b'<AppendedData encoding="raw">' in light_viewable_bytes

        data = Data.get(result["id"])
        assert data is not None
        assert data.light_viewable_file is not None
        assert data.light_viewable_file.endswith(".vtp")

        data_path = Path(app.config["DATA_FOLDER_PATH"]) / result["id"]
        assert (data_path / result["native_file"]).exists()
        assert (data_path / result["viewable_file"]).exists()
        assert (data_path / data.light_viewable_file).exists()
        assert (data_path / data.light_viewable_file).read_bytes() == light_viewable_bytes


def test_generate_files_from_file(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        result = utils_functions.generate_files_from_file(
            GeodeBRep.geode_object_type(), "test.og_brep"
        )

    assert isinstance(result, dict)
    assert result["name"] == "test"
    assert isinstance(result["native_file"], str)
    assert result["native_file"] == "native.og_brep"
    assert isinstance(result["viewable_file"], str)
    assert result["viewable_file"].endswith(".vtm")
    assert isinstance(result["id"], str)
    assert re.match(r"[0-9a-f]{32}", result["id"])
    assert isinstance(result["viewer_type"], str)
    assert isinstance(result["binary_light_viewable"], str)


def test_generate_files_from_file_with_multi_dots(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        result = utils_functions.generate_files_from_file(
            GeodeBRep.geode_object_type(), "cube.test.og_brep"
        )
    assert result["name"] == "cube.test"


def test_generate_files_from_file_returns_geode_id(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        result = utils_functions.generate_files_from_file(
            GeodeBRep.geode_object_type(), "test.og_brep"
        )
        expected_geode_id = GeodeBRep.load(str(data_dir / "test.og_brep")).identifier.id().string()
        assert result["geode_id"] == expected_geode_id
        assert len(result["geode_id"]) == 36
        assert len(result["id"]) == 32
        data = Data.get(result["id"])
        assert data is not None
        assert data.geode_id == expected_geode_id


def test_generate_files_from_file_twice_shares_geode_id(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        first = utils_functions.generate_files_from_file(
            GeodeBRep.geode_object_type(), "test.og_brep"
        )
        second = utils_functions.generate_files_from_file(
            GeodeBRep.geode_object_type(), "test.og_brep"
        )
    assert first["id"] != second["id"]
    assert first["geode_id"] == second["geode_id"]


def test_generate_files_from_non_native_file_twice_shares_geode_id(
    client: FlaskClient,
) -> None:
    app = client.application
    with app.app_context():
        first = utils_functions.generate_files_from_file(
            GeodePolygonalSurface3D.geode_object_type(), "hat.vtp"
        )
        second = utils_functions.generate_files_from_file(
            GeodePolygonalSurface3D.geode_object_type(), "hat.vtp"
        )
        assert first["id"] != second["id"]
        assert first["geode_id"] == second["geode_id"]
        native_path = geode_functions.data_file_path(first["id"], first["native_file"])
        reloaded = GeodePolygonalSurface3D.load(native_path)
        assert reloaded.identifier.id().string() == first["geode_id"]


def test_generate_files_from_object_returns_geode_id(client: FlaskClient) -> None:
    app = client.application
    with app.app_context():
        geode_object = GeodeBRep.load(str(data_dir / "test.og_brep"))
        result = utils_functions.generate_files_from_object(geode_object)
    assert result["geode_id"] == geode_object.identifier.id().string()


def test_send_file_multiple_returns_zip(client: FlaskClient, tmp_path: Path) -> None:
    app = client.application
    with app.app_context():
        app.config["UPLOAD_FOLDER_PATH"] = str(tmp_path)
        file_paths = []
        for i, content in [(1, b"hello 1"), (2, b"hello 2")]:
            file_path = tmp_path / f"tmp_send_file_{i}.txt"
            file_path.write_bytes(content)
            file_paths.append(str(file_path))
        with app.test_request_context():
            response = utils_functions.send_file(
                app.config["UPLOAD_FOLDER_PATH"], file_paths, "bundle"
            )
            assert response.status_code == 200
            assert response.mimetype == "application/zip"
            new_file_name = response.headers.get("new-file-name")
            assert new_file_name == "bundle.zip"
            zip_path = Path(app.config["UPLOAD_FOLDER_PATH"]) / new_file_name
            with zipfile.ZipFile(zip_path, "r") as zip_file:
                zip_entries = zip_file.namelist()
                assert "tmp_send_file_1.txt" in zip_entries
                assert "tmp_send_file_2.txt" in zip_entries
            response.close()


def test_send_file_single_returns_octet_binary(client: FlaskClient, tmp_path: Path) -> None:
    app = client.application
    with app.app_context():
        app.config["UPLOAD_FOLDER_PATH"] = str(tmp_path)
        file_path = tmp_path / "tmp_send_file_1.txt"
        file_path.write_bytes(b"hello 1")
        with app.test_request_context():
            response = utils_functions.send_file(
                app.config["UPLOAD_FOLDER_PATH"],
                [str(file_path)],
                "tmp_send_file_1.txt",
            )
            assert response.status_code == 200
            assert response.mimetype == "application/octet-binary"
            new_file_name = response.headers.get("new-file-name")
            assert new_file_name == "tmp_send_file_1.txt"
            sent_path = Path(app.config["UPLOAD_FOLDER_PATH"]) / new_file_name
            assert sent_path.read_bytes() == b"hello 1"
            response.close()

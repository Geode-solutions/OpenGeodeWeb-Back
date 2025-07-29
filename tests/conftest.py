# Standard library imports
import time
import shutil
import os

# Third party imports
import pytest
import uuid

# Local application imports
from app import app


@pytest.fixture(scope="session", autouse=True)
def copy_data():
    shutil.rmtree("./data", ignore_errors=True)
    shutil.copytree("./tests/data/", "./data/1/", dirs_exist_ok=True)


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "TEST"
    app.config["DATA_FOLDER_PATH"] = "./data/"
    app.config["REQUEST_COUNTER"] = 0
    app.config["LAST_REQUEST_TIME"] = time.time()
    client = app.test_client()
    client.headers = {"Content-type": "application/json", "Accept": "application/json"}
    yield client


@pytest.fixture
def app_context():
    with app.app_context():
        yield


@pytest.fixture
def uuid_project_structure():
    uuid_project = uuid.uuid4().hex
    uuid_data = uuid.uuid4().hex

    base_path = os.path.join("tmp", "vease", uuid_project)
    data_path = os.path.join(base_path, uuid_data)
    uploads_path = os.path.join(base_path, "uploads")

    os.makedirs(data_path, exist_ok=True)
    os.makedirs(uploads_path, exist_ok=True)

    return {
        "uuid_project": uuid_project,
        "uuid_data": uuid_data,
        "base_path": base_path,
        "data_path": data_path,
        "uploads_path": uploads_path,
    }

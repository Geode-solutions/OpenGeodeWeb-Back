# Standard library imports
import time
import shutil

# Third party imports
import os
import pytest

# Local application imports
from app import app
from opengeodeweb_microservice.database.connection import init_database

TEST_ID = "1"


@pytest.fixture(scope="session", autouse=True)
def copy_data():
    shutil.rmtree("./data", ignore_errors=True)
    shutil.copytree("./tests/data/", f"./data/{TEST_ID}/", dirs_exist_ok=True)
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "TEST"
    app.config["DATA_FOLDER_PATH"] = "./data/"
    app.config["UPLOAD_FOLDER"] = "./tests/data/"
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(BASE_DIR, "data", "project.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    print("Current working directory:", os.getcwd())
    print("Directory contents:", os.listdir("."))

    init_database(db_path)


@pytest.fixture
def client():
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
def test_id():
    return TEST_ID

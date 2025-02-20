# Standard library imports
import time
import shutil

# Third party imports
import pytest

# Local application imports
from app import app


@pytest.fixture(scope="session", autouse=True)
def copy_data():
    shutil.rmtree("./data", ignore_errors=True)
    shutil.copytree("./tests/data", "./data", dirs_exist_ok=True)


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

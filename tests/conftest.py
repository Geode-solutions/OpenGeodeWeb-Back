import pytest
from app import app
import time


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

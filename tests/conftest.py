import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "TEST"
    app.config["DATA_FOLDER"] = "./data/"
    client = app.test_client()
    client.headers = {"Content-type": "application/json", "Accept": "application/json"}
    yield client

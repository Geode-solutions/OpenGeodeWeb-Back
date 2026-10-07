from __future__ import annotations

# Standard library imports
import os
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

# Third party imports
from opengeodeweb_microservice.database import connection
from opengeodeweb_microservice.database.connection import init_database

# Local application imports
from opengeodeweb_back.app import create_app, register_ogw_back_blueprints

if TYPE_CHECKING:
    from collections.abc import Generator

    from flask.ctx import AppContext
    from flask.testing import FlaskClient

TEST_ID = "1"

app = create_app(__name__)


@pytest.fixture(scope="session", autouse=True)
def configure_test_environment() -> Generator[None]:
    base_path = Path(__file__).parent.absolute()
    test_data_path = base_path / "data"

    shutil.rmtree("./data", ignore_errors=True)
    shutil.copytree(test_data_path, f"./data/{TEST_ID}/", dirs_exist_ok=True)

    app.config["TESTING"] = True
    app.config["SERVER_NAME"] = "TEST"
    app.config["PROJECT_FOLDER_PATH"] = base_path
    app.config["DATA_FOLDER_PATH"] = "./data/"
    app.config["UPLOAD_FOLDER_PATH"] = "./tests/data/"

    # The database lives in the data folder like in the app (DATA_FOLDER_PATH/project.db),
    # so it is removed with it at session end.
    db_path = (Path(app.config["DATA_FOLDER_PATH"]) / "project.db").resolve()
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"

    init_database(db_path)
    os.environ["TEST_DB_PATH"] = str(db_path)
    register_ogw_back_blueprints(app)
    yield

    connection.close_database()
    tmp_data_path = app.config.get("DATA_FOLDER_PATH")
    if tmp_data_path and Path(tmp_data_path).exists():
        shutil.rmtree(tmp_data_path, ignore_errors=True)


@pytest.fixture
def client() -> FlaskClient:
    app.config["REQUEST_COUNTER"] = 0
    app.config["LAST_REQUEST_TIME"] = time.time()
    return app.test_client()


@pytest.fixture
def app_context() -> Generator[AppContext]:
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def test_id() -> str:
    return TEST_ID

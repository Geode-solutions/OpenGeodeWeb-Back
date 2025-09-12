# Standard library imports
import os
import time

# Third party imports
# Local application imports
from opengeodeweb_microservice.database.connection import get_database

DATABASE_FILENAME = "project.db"


class Config(object):
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", default=False)
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = "5000"
    CORS_HEADERS = "Content-Type"
    UPLOAD_FOLDER = "./uploads"
    REQUEST_COUNTER = 0
    LAST_REQUEST_TIME = time.time()
    LAST_PING_TIME = time.time()
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class ProdConfig(Config):
    SSL = None
    ORIGINS = ""
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    DATA_FOLDER_PATH = "/data"
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.abspath(
        os.path.join(DATA_FOLDER_PATH, DATABASE_FILENAME)
        )}"


class DevConfig(Config):
    SSL = None
    ORIGINS = "*"
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_FOLDER_PATH = os.path.join(BASE_DIR, "data")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(
        BASE_DIR, DATA_FOLDER_PATH, DATABASE_FILENAME
        )}"

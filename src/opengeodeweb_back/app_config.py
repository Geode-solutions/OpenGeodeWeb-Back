# Standard library imports
import os
import time

# Third party imports
# Local application imports


class Config(object):
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", default=False)
    HOST = "localhost"
    PORT = "5000"
    CORS_HEADERS = "Content-Type"
    PROJECT_FOLDER_PATH = "/project"
    DATA_FOLDER_PATH = os.path.join(PROJECT_FOLDER_PATH, "data")
    EXTENSIONS_FOLDER_PATH = os.path.join(PROJECT_FOLDER_PATH, "exensions")
    UPLOAD_FOLDER_PATH = os.path.join(PROJECT_FOLDER_PATH, "uploads")
    REQUEST_COUNTER = 0
    LAST_REQUEST_TIME = time.time()
    LAST_PING_TIME = time.time()
    DATABASE_FILENAME = "project.db"


class ProdConfig(Config):
    SSL = None
    ORIGINS = ""
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    PROJECT_FOLDER_PATH = "/project"


class DevConfig(Config):
    SSL = None
    ORIGINS = "*"
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    PROJECT_FOLDER_PATH = os.path.dirname(os.path.abspath(__file__))

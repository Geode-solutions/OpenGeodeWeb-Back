# Standard library imports
import os
import time

# Third party imports
# Local application imports


class Config(object):
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", default=False)
    DEFAULT_HOST = "localhost"
    DEFAULT_PORT = "5000"
    CORS_HEADERS = "Content-Type"
    UPLOAD_FOLDER = "./uploads"
    DESKTOP_APP = False
    REQUEST_COUNTER = 0
    LAST_REQUEST_TIME = time.time()
    LAST_PING_TIME = time.time()


class ProdConfig(Config):
    SSL = None
    ORIGINS = ""
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    DATA_FOLDER_PATH = "/data/"


class DevConfig(Config):
    SSL = None
    ORIGINS = "*"
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"
    DATA_FOLDER_PATH = "./data/"

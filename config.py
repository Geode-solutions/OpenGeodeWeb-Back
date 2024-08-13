""" Flask configuration """

import os


class Config(object):
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", default=False)
    ID = os.environ.get("ID", default=None)
    PORT = "5000"
    CORS_HEADERS = "Content-Type"
    UPLOAD_FOLDER = "./uploads"
    DATA_FOLDER_PATH = "./data/"
    WORKFLOWS_DATA_FOLDER = "./data_workflows/"
    LOCK_FOLDER = "./lock/"
    TIME_FOLDER = "./time/"


class ProdConfig(Config):
    SSL = None
    ORIGINS = ["*"]
    MINUTES_BEFORE_TIMEOUT = "5"
    SECONDS_BETWEEN_SHUTDOWNS = "150"
    DATA_FOLDER = "/data/"


class DevConfig(Config):
    SSL = None
    ORIGINS = ["*"]
    MINUTES_BEFORE_TIMEOUT = "1000"
    SECONDS_BETWEEN_SHUTDOWNS = "60"
    DATA_FOLDER = "./data/"

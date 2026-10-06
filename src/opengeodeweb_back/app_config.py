# Standard library imports
import os
import time
from pathlib import Path

# Third party imports
# Local application imports

base_dir = Path(__file__).resolve().parent


class Config:
    FLASK_DEBUG = os.environ.get("FLASK_DEBUG", default=False)
    HOST = "localhost"
    PORT = "5000"
    CORS_HEADERS = "Content-Type"
    REQUEST_COUNTER = 0
    LAST_REQUEST_TIME = time.time()
    LAST_PING_TIME = time.time()
    DATABASE_FILENAME = "project.db"

    def __init__(self, project_folder_path: str) -> None:
        self.PROJECT_FOLDER_PATH = project_folder_path
        self.DATA_FOLDER_PATH = str(Path(project_folder_path) / "data")
        self.EXTENSIONS_FOLDER_PATH = str(Path(project_folder_path) / "extensions")
        self.UPLOAD_FOLDER_PATH = str(Path(project_folder_path) / "uploads")


class ProdConfig(Config):
    SSL = None
    ORIGINS = ""
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"


class DevConfig(Config):
    SSL = None
    ORIGINS = "*"
    MINUTES_BEFORE_TIMEOUT = "1"
    SECONDS_BETWEEN_SHUTDOWNS = "10"

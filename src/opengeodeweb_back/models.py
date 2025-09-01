import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, JSON
from .database import db


def generate_uuid():
    return str(uuid.uuid4())


class Data(db.Model):
    __tablename__ = "datas"

    id = db.Column(String, primary_key=True, default=generate_uuid)
    name = db.Column(String, nullable=False)
    native_file_name = db.Column(String, nullable=False)
    viewable_file_name = db.Column(String, nullable=False)
    light_viewable = db.Column(
        String, nullable=True
    )  # Renommé pour correspondre au code
    geode_object = db.Column(String, nullable=False)
    input_files = db.Column(JSON, nullable=True)
    created_at = db.Column(DateTime, default=datetime.now)

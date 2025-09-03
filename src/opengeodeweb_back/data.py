from sqlalchemy import String, JSON
from .database import db


class Data(db.Model):
    __tablename__ = "datas"

    id = db.Column(String, primary_key=True)
    name = db.Column(String, nullable=False)
    native_file_name = db.Column(String, nullable=False)
    viewable_file_name = db.Column(String, nullable=False)
    light_viewable = db.Column(String, nullable=True)
    geode_object = db.Column(String, nullable=False)
    input_file = db.Column(JSON, nullable=True)
    additional_files = db.Column(JSON, nullable=True)

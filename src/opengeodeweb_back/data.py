from sqlalchemy import String, JSON
from .database import database
import uuid
from typing import List


class Data(database.Model):
    __tablename__ = "datas"

    id = database.Column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()).replace("-", "")
    )
    name = database.Column(String, nullable=False)
    native_file_name = database.Column(String, nullable=False)
    viewable_file_name = database.Column(String, nullable=False)
    light_viewable = database.Column(String, nullable=True)
    geode_object = database.Column(String, nullable=False)
    input_file = database.Column(JSON, nullable=True)
    additional_files = database.Column(JSON, nullable=True)

    @staticmethod
    def create(
        name: str, geode_object: str, input_file: str, additional_files: List[str]
    ) -> "Data":
        if additional_files is None:
            additional_files = []

        data_entry = Data(
            name=name,
            geode_object=geode_object,
            input_file=input_file,
            additional_files=additional_files,
            native_file_name="",
            viewable_file_name="",
            light_viewable="",
        )

        database.session.add(data_entry)
        database.session.flush()
        return data_entry

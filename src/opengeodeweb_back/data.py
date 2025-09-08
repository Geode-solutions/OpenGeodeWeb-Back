from sqlalchemy import String, JSON
from sqlalchemy.orm import Mapped, mapped_column
from .database import database, Base
import uuid


class Data(Base):
    __tablename__ = "datas"

    id: Mapped[str] = mapped_column(
        String, primary_key=True, default=lambda: str(uuid.uuid4()).replace("-", "")
    )
    native_file_name: Mapped[str] = mapped_column(String, nullable=False)
    viewable_file_name: Mapped[str] = mapped_column(String, nullable=False)
    geode_object: Mapped[str] = mapped_column(String, nullable=False)

    light_viewable: Mapped[str | None] = mapped_column(String, nullable=True)
    input_file: Mapped[str | None] = mapped_column(String, nullable=True)
    additional_files: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    @staticmethod
    def create(
        geode_object: str,
        input_file: str | None = None,
        additional_files: list[str] | None = None,
    ) -> "Data":
        input_file = input_file if input_file is not None else ""
        additional_files = additional_files if additional_files is not None else []

        data_entry = Data(
            geode_object=geode_object,
            input_file=input_file,
            additional_files=additional_files,
            native_file_name="",
            viewable_file_name="",
            light_viewable=None,
        )

        database.session.add(data_entry)
        database.session.flush()
        return data_entry

    @staticmethod
    def get(data_id: str) -> "Data | None":
        return database.session.get(Data, data_id)

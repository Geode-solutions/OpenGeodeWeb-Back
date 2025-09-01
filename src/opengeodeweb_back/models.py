import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.orm import declarative_base

Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Data(Base):
    __tablename__ = "datas"

    id = Column(String, primary_key=True, default=generate_uuid)
    name = Column(String, nullable=False)
    native_file_name = Column(String, nullable=False)
    viewable_file_name = Column(String, nullable=False)
    binary_light_viewable = Column(String, nullable=True) 
    geode_object = Column(String, nullable=False)
    input_files = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.now)

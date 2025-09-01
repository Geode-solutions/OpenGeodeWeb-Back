from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_engine(db_path: str):
    return create_engine(f"sqlite:///{db_path}", echo=False)


def get_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()

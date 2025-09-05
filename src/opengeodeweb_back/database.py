from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase

DATABASE_FILENAME = "project.db"


class Base(DeclarativeBase):
    pass


database = SQLAlchemy(model_class=Base)


def initialize_database(app: Flask) -> SQLAlchemy:
    database.init_app(app)
    with app.app_context():
        database.create_all()
    return database

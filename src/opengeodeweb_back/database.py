from flask import Flask
from flask_sqlalchemy import SQLAlchemy

DATABASE_FILENAME = "project.db"

database = SQLAlchemy()


def initialize_database(app: Flask) -> SQLAlchemy:
    database.init_app(app)
    with app.app_context():
        database.create_all()
    return database

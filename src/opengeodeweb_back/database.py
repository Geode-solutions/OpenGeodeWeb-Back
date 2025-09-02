from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

initialized = False


def init_db(app):
    global initialized
    if initialized:
        return db
    print("DB", app.config.get("SQLALCHEMY_DATABASE_URI"))
    db.init_app(app)
    with app.app_context():
        db.create_all()
    initialized = True
    return db

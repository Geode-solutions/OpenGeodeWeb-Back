"""Packages"""

import os

import flask
import flask_cors
from werkzeug.exceptions import HTTPException

from src.opengeodeweb_back.routes import blueprint_routes
from src.opengeodeweb_back.routes.models import blueprint_models
from src.opengeodeweb_back.utils_functions import handle_exception
from src.opengeodeweb_back import app_config
from opengeodeweb_microservice.database.connection import init_database


""" Global config """
app = flask.Flask(__name__)

""" Config variables """
FLASK_DEBUG = True if os.environ.get("FLASK_DEBUG", default=None) == "True" else False

if FLASK_DEBUG == False:
    app.config.from_object(app_config.ProdConfig)
else:
    app.config.from_object(app_config.DevConfig)

DEFAULT_HOST = app.config.get("DEFAULT_HOST")
PORT = int(app.config.get("DEFAULT_PORT"))
ORIGINS = app.config.get("ORIGINS")
SSL = app.config.get("SSL")

flask_cors.CORS(app, origins=ORIGINS)
app.register_blueprint(
    blueprint_routes.routes,
    url_prefix="/",
    name="blueprint_routes",
)

app.register_blueprint(
    blueprint_models.routes,
    url_prefix="/models",
    name="blueprint_models",
)


@app.errorhandler(HTTPException)
def errorhandler(e):
    return handle_exception(e)


@app.route(
    "/error",
    methods=["POST"],
)
def return_error():
    flask.abort(500, f"Test")


# ''' Main '''
if __name__ == "__main__":
    init_database(app)
    print(f"Python is running in {FLASK_DEBUG} mode")
    app.run(debug=FLASK_DEBUG, host=DEFAULT_HOST, port=PORT, ssl_context=SSL)

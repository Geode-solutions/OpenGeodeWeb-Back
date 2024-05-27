""" Packages """

import os

import flask
import flask_cors
from werkzeug.exceptions import HTTPException

from src.opengeodeweb_back.routes import blueprint_routes
from src.opengeodeweb_back.geode_functions import handle_exception


""" Global config """
app = flask.Flask(__name__)

""" Config variables """
FLASK_DEBUG = True if os.environ.get("FLASK_DEBUG", default=None) == "True" else False

if FLASK_DEBUG == False:
    app.config.from_object("config.ProdConfig")
else:
    app.config.from_object("config.DevConfig")


PORT = int(app.config.get("PORT"))
ORIGINS = app.config.get("ORIGINS")
SSL = app.config.get("SSL")

flask_cors.CORS(app, origins=ORIGINS)
app.register_blueprint(
    blueprint_routes.routes,
    url_prefix="/",
    name="blueprint_routes",
)


@app.errorhandler(HTTPException)
def errorhandler(e):
    # print("tutu", e, flush=True)
    return handle_exception(e)


@app.route(
    "/error",
    methods=["POST"],
)
def return_error():
    # print("return_error 123", flush=True)
    flask.abort(500, f"Test")
    # return flask.make_response({}, 500)


# ''' Main '''
if __name__ == "__main__":
    print(f"Python is running in {FLASK_DEBUG} mode")
    app.run(debug=FLASK_DEBUG, host="0.0.0.0", port=PORT, ssl_context=SSL)

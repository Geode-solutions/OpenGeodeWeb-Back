""" Packages """

import os

import flask
import flask_cors
from werkzeug.exceptions import HTTPException

from werkzeug.exceptions import HTTPException

from src.opengeodeweb_back.routes import blueprint_routes


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
def handle_exception(e):
    response = e.get_response()
    response.data = flask.json.dumps(
        {
            "code": e.code,
            "name": e.name,
            "description": e.description,
        }
    )
    response.content_type = "application/json"
    return response


# ''' Main '''
if __name__ == "__main__":
    print(f"Python is running in {FLASK_DEBUG} mode")
    app.run(debug=FLASK_DEBUG, host="0.0.0.0", port=PORT, ssl_context=SSL)

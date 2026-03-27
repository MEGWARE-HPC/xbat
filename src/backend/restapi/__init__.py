from shared.configuration import set_logger, set_app, set_config

NAME = "restapi"

set_logger(NAME)
set_app(NAME)

import sys
import yaml
import logging
import logging.config
import logging.handlers
import os
import secrets
from pathlib import Path

from shared.helpers import overwrite_log_level, get_service_configuration
from shared.files import read_file_to_str
from shared.exceptionHandler import handle_exception
from shared.jsonProvider import CustomJSONProvider

DATABASE_MAINTENANCE_SLEEP = 10
OPENAPI_PATH = Path().absolute() / NAME / "api" / "openapi.yml"
TEMPLATE_FOLDER = Path().absolute() / NAME / "templates"
LOGGING_CONFIG_PATH = Path().absolute().parent / "shared" / "logging.conf"

sys.excepthook = handle_exception

from connexion import FlaskApp
from connexion.middleware import MiddlewarePosition
from starlette.middleware.cors import CORSMiddleware

app = FlaskApp(
    NAME,
    specification_dir="api/",
    #  options={'swagger_path': 'restapi/swagger'},
    server_args={'template_folder': str(TEMPLATE_FOLDER)})

flask_app = app.app

flask_app.json = CustomJSONProvider(flask_app)

app.add_middleware(
    CORSMiddleware,
    position=MiddlewarePosition.BEFORE_EXCEPTION,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def configure():
    service_configuration = get_service_configuration()

    openapi = yaml.full_load(read_file_to_str(str(OPENAPI_PATH)))
    settings = {
        "openapi":
        openapi,
        "security_roles":
        openapi["components"]["securitySchemes"]["oauth2"]["flows"]["implicit"]
        ["x-scopesUser"],
        "CONFIG":
        service_configuration,
        "BUILD":
        os.getenv('BUILD', "dev"),
        "DEMO_MODE":
        service_configuration["demo"]["enabled"] == "true"
        if "demo" in service_configuration
        and "enabled" in service_configuration["demo"] else False,
        "SECRET_KEY":
        os.getenv('FLASK_SECRET_KEY', secrets.token_hex(16))
    }

    flask_app.config.update(**settings)
    set_config(service_configuration)
    logging.config.fileConfig(LOGGING_CONFIG_PATH,
                              disable_existing_loggers=False)
    overwrite_log_level(NAME, service_configuration["general"]["log_level"])


def create_app():
    with flask_app.app_context():
        configure()

        @flask_app.after_request
        def after_request(response):
            # Add CORS headers for access from different domain
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers",
                                 "Content-Type,Authorization")
            response.headers.add("Access-Control-Allow-Methods",
                                 "GET,PUT,POST,PATCH,DELETE,OPTIONS")
            if response.status_code == 204 and response.headers['Content-Type']:
                response.headers.pop("Content-Type", None)
                response.headers.pop("Content-Length", None)
            return response

        from werkzeug.exceptions import HTTPException
        from backend.restapi.mod_oauth import config_oauth
        from backend.restapi.auth import oauth_routes

        # @flask_app.before_request
        # def before_request():
        #     print(request.endpoint)
        #     pass

        @flask_app.errorhandler(HTTPException)
        def http_error_handler(e):
            from flask import json
            """Return JSON instead of HTML for HTTP errors."""
            # start with the correct headers and status code from the error
            response = e.get_response()
            # replace the body with JSON
            # TODO check other available information
            response.data = json.dumps({
                "title": e.name,
                "detail": e.description,
                "status": e.code,
            })
            response.content_type = "application/json"

            return response

        config_oauth(flask_app)
        flask_app.register_blueprint(oauth_routes.bp, url_prefix="/oauth")

        app.add_api(OPENAPI_PATH)

        return app


if __name__ == '__main__':
    app = create_app()
    app.run(
        host="0.0.0.0",
        port=7000,
    )
    # ssl_context=("../../dev/certs/cert.pem", "../../dev/certs/key.pem")
    # app.run(host="0.0.0.0", port=7001)

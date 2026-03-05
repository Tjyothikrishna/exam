from flask import Flask

from .config import Config
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)
    register_blueprints(app)
    return app

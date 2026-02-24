from flask import Flask

from .routes import register_routes


def create_app():
    app = Flask(__name__)
    app.secret_key = "your_secret_key"

    register_routes(app)
    return app

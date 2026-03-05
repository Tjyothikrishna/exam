from flask import Flask

from .config import Config
from .models import db, migrate
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app

from flask import Flask

from .config import get_config_class
from .extensions import bcrypt, login_manager
from .models import User, db, migrate
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(get_config_class())

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    register_blueprints(app)

    with app.app_context():
        db.create_all()

    return app

from flask import Flask

from .config import Config
from .extensions import bcrypt, login_manager
from .models import User, db, migrate
from .routes import register_blueprints


def create_app() -> Flask:
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.config.from_object(Config)

    db.init_app(app)
    migrate.init_app(app, db)
    bcrypt.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    register_blueprints(app)

    @app.get("/")
    def index():
        from flask import redirect, url_for
        return redirect(url_for("auth.login"))


    with app.app_context():
        db.create_all()

    return app

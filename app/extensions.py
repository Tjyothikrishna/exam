from flask_login import LoginManager

try:
    from flask_bcrypt import Bcrypt
except Exception:  # fallback in restricted env
    from werkzeug.security import check_password_hash, generate_password_hash

    class Bcrypt:  # type: ignore
        def init_app(self, app):
            return None

        def generate_password_hash(self, password: str):
            return generate_password_hash(password).encode("utf-8")

        def check_password_hash(self, pw_hash, password: str) -> bool:
            if isinstance(pw_hash, bytes):
                pw_hash = pw_hash.decode("utf-8")
            return check_password_hash(pw_hash, password)


bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = "auth.login"

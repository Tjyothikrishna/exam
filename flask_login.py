"""Lightweight fallback for Flask-Login in restricted environments."""

from functools import wraps

from flask import abort


class UserMixin:
    @property
    def is_authenticated(self):
        return True

    def get_id(self):
        return str(getattr(self, "id", ""))


class _Anonymous:
    is_authenticated = False
    role = None
    id = None


current_user = _Anonymous()


class LoginManager:
    def __init__(self):
        self.login_view = None
        self._loader = None

    def init_app(self, app):
        return None

    def user_loader(self, callback):
        self._loader = callback
        return callback


def login_user(user):
    global current_user
    current_user = user


def logout_user():
    global current_user
    current_user = _Anonymous()


def login_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not getattr(current_user, "is_authenticated", False):
            abort(401)
        return func(*args, **kwargs)

    return wrapper

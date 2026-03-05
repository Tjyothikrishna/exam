"""Lightweight local fallback for Flask-Migrate in restricted environments."""


class Migrate:
    def __init__(self, app=None, db=None):
        self.app = app
        self.db = db

    def init_app(self, app, db):
        self.app = app
        self.db = db

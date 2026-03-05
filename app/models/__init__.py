from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

from .db import get_db_connection


db = SQLAlchemy()
migrate = Migrate()


from .entities import Exam, Question, Result, User  # noqa: E402,F401

__all__ = [
    "db",
    "migrate",
    "get_db_connection",
    "User",
    "Exam",
    "Question",
    "Result",
]

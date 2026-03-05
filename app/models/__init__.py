from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()
migrate = Migrate()


from .entities import Option, Question, QuestionSet, StudentAnswer, TestAttempt, User  # noqa: E402,F401

__all__ = [
    "db",
    "migrate",
    "User",
    "QuestionSet",
    "Question",
    "Option",
    "TestAttempt",
    "StudentAnswer",
]

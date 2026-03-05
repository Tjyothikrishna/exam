from datetime import datetime

from flask_login import UserMixin

from . import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    mobile_number = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="student")
    gender = db.Column(db.String(10))
    profile_picture = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    attempts = db.relationship("TestAttempt", back_populates="student", cascade="all, delete-orphan")


class QuestionSet(db.Model):
    __tablename__ = "question_sets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    duration = db.Column(db.Integer, nullable=False, default=60)
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    questions = db.relationship("Question", back_populates="question_set", cascade="all, delete-orphan")


class Question(db.Model):
    __tablename__ = "questions"

    id = db.Column(db.Integer, primary_key=True)
    question_set_id = db.Column(db.Integer, db.ForeignKey("question_sets.id"), nullable=False, index=True)
    question_text = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    question_set = db.relationship("QuestionSet", back_populates="questions")
    options = db.relationship("Option", back_populates="question", cascade="all, delete-orphan")


class Option(db.Model):
    __tablename__ = "options"

    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
    option_text = db.Column(db.String(255), nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)

    question = db.relationship("Question", back_populates="options")


class TestAttempt(db.Model):
    __tablename__ = "test_attempts"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    question_set_id = db.Column(db.Integer, db.ForeignKey("question_sets.id"), nullable=False, index=True)
    score = db.Column(db.Integer, nullable=False, default=0)
    total_questions = db.Column(db.Integer, nullable=False, default=0)
    percentage = db.Column(db.Float)
    passed = db.Column(db.Boolean)
    attempted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    student = db.relationship("User", back_populates="attempts")
    question_set = db.relationship("QuestionSet")
    answers = db.relationship("StudentAnswer", back_populates="attempt", cascade="all, delete-orphan")


class StudentAnswer(db.Model):
    __tablename__ = "student_answers"

    id = db.Column(db.Integer, primary_key=True)
    test_attempt_id = db.Column(db.Integer, db.ForeignKey("test_attempts.id"), nullable=False, index=True)
    question_id = db.Column(db.Integer, db.ForeignKey("questions.id"), nullable=False, index=True)
    selected_option_id = db.Column(db.Integer, db.ForeignKey("options.id"), nullable=False, index=True)
    is_correct = db.Column(db.Boolean, nullable=False, default=False)
    answered_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    attempt = db.relationship("TestAttempt", back_populates="answers")

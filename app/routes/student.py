from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.models import Exam, Question, Result, db
from .common import student_required

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/dashboard")
@login_required
@student_required
def dashboard():
    total_attempts = Result.query.filter_by(student_id=current_user.id).count()
    recent_results = (
        Result.query.filter_by(student_id=current_user.id)
        .order_by(Result.submitted_at.desc())
        .limit(5)
        .all()
    )
    return render_template(
        "student/dashboard.html",
        total_attempts=total_attempts,
        recent_results=recent_results,
    )


@bp.route("/home")
@login_required
@student_required
def home():
    return redirect(url_for("student.dashboard"))


@bp.route("/exams")
@login_required
@student_required
def exams():
    exams_list = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template("student/exams.html", exams=exams_list)


@bp.route("/exam/<int:exam_id>/start")
@login_required
@student_required
def start_exam(exam_id: int):
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam.id).order_by(Question.id.asc()).all()

    if not questions:
        flash("This exam has no questions yet.", "warning")
        return redirect(url_for("student.exams"))

    session["active_exam_id"] = exam.id
    return render_template("student/exam.html", exam=exam, questions=questions)


@bp.post("/exam/<int:exam_id>/submit")
@login_required
@student_required
def submit_exam(exam_id: int):
    exam = Exam.query.get_or_404(exam_id)
    questions = Question.query.filter_by(exam_id=exam.id).all()

    if not questions:
        flash("No questions found for this exam.", "danger")
        return redirect(url_for("student.exams"))

    correct = 0
    for question in questions:
        selected = request.form.get(f"question_{question.id}", "").strip().upper()
        if selected and selected == question.correct_answer.upper():
            correct += 1

    total = len(questions)
    score = round((correct / total) * 100, 2) if total else 0

    result = Result(student_id=current_user.id, exam_id=exam.id, score=score)
    db.session.add(result)
    db.session.commit()

    session.pop("active_exam_id", None)

    return render_template(
        "student/result.html",
        exam=exam,
        correct=correct,
        total=total,
        score=score,
        result=result,
    )

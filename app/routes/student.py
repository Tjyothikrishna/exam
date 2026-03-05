from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.models import Exam, Question, Result, db
from app.services.exam_service import load_random_question_set, save_attempt
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
    return render_template("home.html", user=current_user, total_attempts=0, last_attempt=None, performance_trend=None, avg_percentage=0)


@bp.route("/test")
@login_required
@student_required
def test():
    questions, question_set_id = load_random_question_set()
    if not questions:
        flash("No question sets available.", "danger")
        return redirect(url_for("student.home"))

    session["questions"] = questions
    session["question_set_id"] = question_set_id
    session["current_index"] = 0
    session["score"] = 0
    session["answers"] = []
    return redirect(url_for("student.question"))


@bp.route("/question", methods=["GET", "POST"])
@login_required
@student_required
def question():
    questions = session.get("questions", [])
    index = session.get("current_index", 0)

    if not questions:
        return redirect(url_for("student.home"))
    if index >= len(questions):
        return redirect(url_for("student.test_result"))

    current_question = questions[index]

    if request.method == "POST":
        selected_option_id = int(request.form.get("option"))
        is_correct = selected_option_id == current_question.get("correct_option_id")
        if is_correct:
            session["score"] = session.get("score", 0) + 1

        answers = session.get("answers", [])
        answers.append(
            {
                "question_id": current_question["id"],
                "selected_option_id": selected_option_id,
                "is_correct": is_correct,
            }
        )
        session["answers"] = answers
        session["current_index"] = index + 1
        return redirect(url_for("student.question"))

    return render_template(
        "question.html",
        question={
            "question": current_question.get("question_text"),
            "options": [
                {"id": opt["id"], "text": opt["option_text"]}
                for opt in current_question.get("options", [])
            ],
        },
        index=index + 1,
        total=len(questions),
        feedback=None,
    )


@bp.route("/test_result")
@login_required
@student_required
def test_result():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("student.home"))
    total = len(questions)
    score = session.get("score", 0)
    percentage = round((score / total) * 100, 2) if total else 0
    return render_template("test_result.html", score=score, total=total, percentage=percentage)


@bp.route("/submit_test", methods=["POST"])
@login_required
@student_required
def submit_test():
    questions = session.get("questions", [])
    answers = session.get("answers", [])
    question_set_id = session.get("question_set_id")
    save_attempt(current_user.id, question_set_id, questions, answers, session.get("score", 0))
    save_attempt(session["user_id"], question_set_id, questions, answers, session.get("score", 0))

    for key in ["questions", "answers", "score", "current_index", "question_set_id"]:
        session.pop(key, None)

    return redirect(url_for("student.home"))

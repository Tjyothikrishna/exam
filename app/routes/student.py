from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.services.exam_service import load_random_question_set, save_attempt
from .common import student_required

bp = Blueprint("student", __name__, url_prefix="/student")


@bp.route("/home")
@login_required
@student_required
def home():
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

    for key in ["questions", "answers", "score", "current_index", "question_set_id"]:
        session.pop(key, None)

    return redirect(url_for("student.home"))

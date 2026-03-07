from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.models import TestAttempt
from app.services.exam_service import load_random_question_set, save_attempt
from .common import student_required

bp = Blueprint("student", __name__)


@bp.route("/home", endpoint="home")
@login_required
@student_required
def home():
    attempts_query = TestAttempt.query.filter_by(user_id=current_user.id).order_by(TestAttempt.attempted_at.desc())
    all_attempts = attempts_query.all()
    total_attempts = len(all_attempts)
    last_attempt = all_attempts[0] if all_attempts else None

    performance_trend = None
    if len(all_attempts) >= 2:
        if all_attempts[0].percentage > all_attempts[1].percentage:
            performance_trend = "Improved"
        elif all_attempts[0].percentage < all_attempts[1].percentage:
            performance_trend = "Declined"
        else:
            performance_trend = "Same"

    avg_percentage = round(sum(a.percentage or 0 for a in all_attempts) / total_attempts, 2) if total_attempts else 0
    best_score = round(max((a.percentage or 0) for a in all_attempts), 2) if all_attempts else 0

    page = request.args.get("page", 1, type=int)
    attempts_page = attempts_query.paginate(page=page, per_page=25, error_out=False)

    return render_template(
        "student_home.html",
        user=current_user,
        total_attempts=total_attempts,
        last_attempt=last_attempt,
        performance_trend=performance_trend,
        avg_percentage=avg_percentage,
        best_score=best_score,
        attempts_page=attempts_page,
    )


@bp.route("/test", endpoint="test")
@login_required
@student_required
def test():
    questions, question_set_id = load_random_question_set()
    if not questions:
        flash("No question sets available.")
        return redirect(url_for("student.home"))

    session["questions"] = questions
    session["question_set_id"] = question_set_id
    session["current_index"] = 0
    session["score"] = 0
    session["answers"] = []
    return redirect(url_for("student.question"))


@bp.route("/question", methods=["GET", "POST"], endpoint="question")
@login_required
@student_required
def question():
    questions = session.get("questions", [])
    index = session.get("current_index", 0)

    if not questions:
        return redirect(url_for("student.home"))

    if request.method == "POST":
        selected_option_id = int(request.form.get("option", "0"))
        current_question = questions[index]
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

        if session["current_index"] >= len(questions):
            return redirect(url_for("student.submit_test"))
        return redirect(url_for("student.question"))

    if index >= len(questions):
        return redirect(url_for("student.submit_test"))

    current_question = questions[index]
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


@bp.route("/submit_test", methods=["GET", "POST"], endpoint="submit_test")
@login_required
@student_required
def submit_test():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("student.home"))

    attempt = save_attempt(
        current_user.id,
        session.get("question_set_id"),
        questions,
        session.get("answers", []),
        session.get("score", 0),
    )

    score = session.get("score", 0)
    total = len(questions)
    percentage = attempt.percentage

    for key in ["questions", "answers", "score", "current_index", "question_set_id"]:
        session.pop(key, None)

    return render_template("test_result.html", score=score, total=total, percentage=percentage)

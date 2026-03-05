from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models import get_db_connection
from app.routes.common import login_required
from app.services.exam_service import load_random_question_set, save_attempt

bp = Blueprint("student", __name__)


@bp.route("/home", endpoint="home")
@login_required
def home():
    user_id = session["user_id"]

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT id, first_name, last_name, email, mobile_number, gender, profile_picture, role
        FROM users WHERE id = %s
        """,
        (user_id,),
    )
    user = cursor.fetchone()

    if not user or user["role"] != "student":
        cursor.close()
        conn.close()
        return redirect(url_for("auth.login"))

    cursor.execute("SELECT COUNT(*) AS total_attempts FROM test_attempts WHERE user_id = %s", (user_id,))
    total_attempts = cursor.fetchone()["total_attempts"]

    cursor.execute(
        """
        SELECT ta.score, ta.total_questions, ta.percentage, ta.passed, ta.attempted_at, qs.title AS test_name
        FROM test_attempts ta JOIN question_sets qs ON ta.question_set_id = qs.id
        WHERE ta.user_id = %s ORDER BY ta.attempted_at DESC LIMIT 1
        """,
        (user_id,),
    )
    last_attempt = cursor.fetchone()

    cursor.execute("SELECT ROUND(AVG(percentage), 2) AS avg_percentage FROM test_attempts WHERE user_id = %s", (user_id,))
    avg_percentage = cursor.fetchone()["avg_percentage"]

    cursor.close()
    conn.close()

    return render_template(
        "home.html",
        user=user,
        total_attempts=total_attempts,
        last_attempt=last_attempt,
        performance_trend=None,
        avg_percentage=avg_percentage,
    )


@bp.route("/test", endpoint="test")
@login_required
def test():
    questions, question_set_id = load_random_question_set()
    if not questions:
        flash("No question sets available.", "danger")
        return redirect(url_for("home"))

    session["questions"] = questions
    session["question_set_id"] = question_set_id
    session["current_index"] = 0
    session["score"] = 0
    session["answers"] = []
    return redirect(url_for("question"))


@bp.route("/question", methods=["GET", "POST"], endpoint="question")
@login_required
def question():
    questions = session.get("questions", [])
    index = session.get("current_index", 0)

    if not questions:
        return redirect(url_for("home"))
    if index >= len(questions):
        return redirect(url_for("test_result"))

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
        return redirect(url_for("question"))

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


@bp.route("/test_result", endpoint="test_result")
@login_required
def test_result():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("home"))
    total = len(questions)
    score = session.get("score", 0)
    percentage = round((score / total) * 100, 2) if total else 0
    return render_template("test_result.html", score=score, total=total, percentage=percentage)


@bp.route("/submit_test", methods=["POST"], endpoint="submit_test")
@login_required
def submit_test():
    questions = session.get("questions", [])
    answers = session.get("answers", [])
    question_set_id = session.get("question_set_id")
    save_attempt(session["user_id"], question_set_id, questions, answers, session.get("score", 0))

    for key in ["questions", "answers", "score", "current_index", "question_set_id"]:
        session.pop(key, None)

    return redirect(url_for("home"))


@bp.route("/about", endpoint="about")
def about():
    return render_template("about.html")


@bp.route("/help", methods=["GET"], endpoint="help")
def help_page():
    return render_template("help.html")


@bp.route("/settings", methods=["GET"], endpoint="settings")
@login_required
def settings():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (session["user_id"],))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template("settings.html", user=user, user_name=session.get("user_name"))

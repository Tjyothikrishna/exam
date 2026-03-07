from datetime import datetime, timedelta, timezone

from flask import Blueprint, jsonify, flash, redirect, render_template, request, session, url_for
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required

from app.models import QuestionSet, TestAttempt
from app.services.exam_service import load_random_question_set, save_attempt
from .common import student_required

bp = Blueprint("student", __name__)


def _clamp_question_index(index: int, total: int) -> int:
    if total <= 0:
        return 0
    return max(0, min(index, total - 1))


def _remaining_seconds_from_session() -> int:
    exam_ends_at = session.get("exam_ends_at")
    if not exam_ends_at:
        return 0
    try:
        ends_at = datetime.fromisoformat(exam_ends_at)
        if ends_at.tzinfo is None:
            ends_at = ends_at.replace(tzinfo=timezone.utc)
        return max(0, int((ends_at - datetime.now(timezone.utc)).total_seconds()))
    except ValueError:
        return 0


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

    trend_attempts = list(reversed(all_attempts[:25]))
    chart_data = {
        "labels": [a.attempted_at.strftime("%d %b") for a in trend_attempts],
        "scores": [float(a.percentage or 0) for a in trend_attempts],
        "average": [avg_percentage for _ in trend_attempts],
        "total_exams": total_attempts,
    }

    return render_template(
        "student_home.html",
        user=current_user,
        total_attempts=total_attempts,
        last_attempt=last_attempt,
        performance_trend=performance_trend,
        avg_percentage=avg_percentage,
        best_score=best_score,
        attempts_page=attempts_page,
        chart_data=chart_data,
    )


@bp.route("/test", endpoint="test")
@login_required
@student_required
def test():
    questions, question_set_id = load_random_question_set()
    if not questions:
        flash("No question sets available.")
        return redirect(url_for("student.home"))

    question_set = QuestionSet.query.get(question_set_id)
    duration_minutes = int(question_set.duration) if question_set and question_set.duration else 30

    session["questions"] = questions
    session["question_set_id"] = question_set_id
    session["current_index"] = 0
    session["answers_map"] = {}
    session["flagged_map"] = {}
    session["exam_duration_minutes"] = duration_minutes
    session["exam_ends_at"] = (datetime.now(timezone.utc) + timedelta(minutes=duration_minutes)).isoformat()

    return redirect(url_for("student.question", q=0))


@bp.route("/question", methods=["GET", "POST"], endpoint="question")
@login_required
@student_required
def question():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("student.home"))

    total = len(questions)
    current_index = _clamp_question_index(request.args.get("q", session.get("current_index", 0), type=int), total)

    answers_map = session.get("answers_map", {})
    flagged_map = session.get("flagged_map", {})

    if request.method == "POST":
        current_index = _clamp_question_index(int(request.form.get("current_index", current_index)), total)
        current_question = questions[current_index]
        qid_key = str(current_question["id"])

        selected_option_raw = request.form.get("option")
        if selected_option_raw:
            answers_map[qid_key] = int(selected_option_raw)
            session["answers_map"] = answers_map

        action = request.form.get("action", "next")

        if action == "autosave":
            flagged_map[qid_key] = request.form.get("flagged", "0") == "1"
            session["flagged_map"] = flagged_map
            return jsonify({"ok": True})

        if action == "flag_toggle":
            flagged_map[qid_key] = not bool(flagged_map.get(qid_key, False))
            session["flagged_map"] = flagged_map


    answers_map = session.get("answers_map", {})

    if request.method == "POST":
        current_index = _clamp_question_index(int(request.form.get("current_index", current_index)), total)
        current_question = questions[current_index]

        selected_option_raw = request.form.get("option")
        if selected_option_raw:
            answers_map[str(current_question["id"])] = int(selected_option_raw)
            session["answers_map"] = answers_map

        action = request.form.get("action", "next")
        if action == "prev":
            target_index = _clamp_question_index(current_index - 1, total)
            session["current_index"] = target_index
            return redirect(url_for("student.question", q=target_index))

        if action == "go":
            target_index = _clamp_question_index(int(request.form.get("target_index", current_index)), total)
            session["current_index"] = target_index
            return redirect(url_for("student.question", q=target_index))

        if action == "review":
            return redirect(url_for("student.review_exam"))

        target_index = _clamp_question_index(current_index + 1, total)
        session["current_index"] = target_index
        return redirect(url_for("student.question", q=target_index))

    session["current_index"] = current_index
    current_question = questions[current_index]
    qid_key = str(current_question["id"])

    selected_option_id = answers_map.get(qid_key)

    palette = []
    for idx, q in enumerate(questions):
        q_key = str(q["id"])
        palette.append(
            {
                "index": idx,
                "number": idx + 1,
                "is_current": idx == current_index,
                "is_answered": q_key in answers_map,
                "is_flagged": bool(flagged_map.get(q_key, False)),
            }
        )

        if action == "submit":
            return redirect(url_for("student.submit_test"))

        target_index = _clamp_question_index(current_index + 1, total)
        session["current_index"] = target_index
        return redirect(url_for("student.question", q=target_index))

    session["current_index"] = current_index
    current_question = questions[current_index]

    selected_option_id = answers_map.get(str(current_question["id"]))
    answered_indexes = {
        idx for idx, q in enumerate(questions) if str(q["id"]) in answers_map
    }

    remaining_seconds = 0
    exam_ends_at = session.get("exam_ends_at")
    if exam_ends_at:
        try:
            ends_at = datetime.fromisoformat(exam_ends_at)
            if ends_at.tzinfo is None:
                ends_at = ends_at.replace(tzinfo=timezone.utc)
            remaining_seconds = max(0, int((ends_at - datetime.now(timezone.utc)).total_seconds()))
        except ValueError:
            remaining_seconds = 0

    return render_template(
        "question.html",
        question={
            "id": current_question.get("id"),
            "question": current_question.get("question_text"),
            "options": [
                {"id": opt["id"], "text": opt["option_text"]}
                for opt in current_question.get("options", [])
            ],
        },
        index=current_index + 1,
        total=total,
        selected_option_id=selected_option_id,
        remaining_seconds=_remaining_seconds_from_session(),
        palette=palette,
        is_flagged=bool(flagged_map.get(qid_key, False)),
    )


@bp.route("/review_exam", endpoint="review_exam")
@login_required
@student_required
def review_exam():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("student.home"))

    answers_map = session.get("answers_map", {})
    flagged_map = session.get("flagged_map", {})

    total = len(questions)
    answered = len(answers_map)
    flagged = sum(1 for q in questions if flagged_map.get(str(q["id"]), False))
    unanswered = max(0, total - answered)

    palette = []
    for idx, q in enumerate(questions):
        q_key = str(q["id"])
        palette.append(
            {
                "index": idx,
                "number": idx + 1,
                "is_answered": q_key in answers_map,
                "is_flagged": bool(flagged_map.get(q_key, False)),
            }
        )

    return render_template(
        "exam_review.html",
        total=total,
        answered=answered,
        unanswered=unanswered,
        flagged=flagged,
        palette=palette,
        remaining_seconds=_remaining_seconds_from_session(),
        answered_indexes=answered_indexes,
        remaining_seconds=remaining_seconds,
    )


@bp.route("/submit_test", methods=["GET", "POST"], endpoint="submit_test")
@login_required
@student_required
def submit_test():
    questions = session.get("questions", [])
    if not questions:
        return redirect(url_for("student.home"))

    answers_map = session.get("answers_map", {})
    answers = []
    score = 0

    for question in questions:
        selected_option_id = answers_map.get(str(question.get("id")))
        if selected_option_id is None:
            continue
        is_correct = int(selected_option_id) == int(question.get("correct_option_id") or 0)
        if is_correct:
            score += 1
        answers.append(
            {
                "question_id": question["id"],
                "selected_option_id": int(selected_option_id),
                "is_correct": is_correct,
            }
        )

    attempt = save_attempt(
        current_user.id,
        session.get("question_set_id"),
        questions,
        answers,
        score,
    )

    total = len(questions)
    percentage = attempt.percentage

    for key in [
        "questions",
        "answers_map",
        "flagged_map",
        "current_index",
        "question_set_id",
        "exam_duration_minutes",
        "exam_ends_at",
    ]:
        session.pop(key, None)

    return render_template("test_result.html", score=score, total=total, percentage=percentage)

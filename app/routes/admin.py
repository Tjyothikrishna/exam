from collections import OrderedDict

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Option, Question, QuestionSet, TestAttempt, User, db
from app.routes.common import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard", endpoint="admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    attempts = TestAttempt.query.all()
    stats = {
        "total_students": User.query.filter_by(role="student").count(),
        "total_exams": QuestionSet.query.count(),
        "total_questions": Question.query.count(),
        "total_results": len(attempts),
    }
    recent_exams = QuestionSet.query.order_by(QuestionSet.created_at.desc()).limit(5).all()

    distribution_ranges = OrderedDict([("0-20", 0), ("21-40", 0), ("41-60", 0), ("61-80", 0), ("81-100", 0)])
    for attempt in attempts:
        score = float(attempt.percentage or 0)
        if score <= 20:
            distribution_ranges["0-20"] += 1
        elif score <= 40:
            distribution_ranges["21-40"] += 1
        elif score <= 60:
            distribution_ranges["41-60"] += 1
        elif score <= 80:
            distribution_ranges["61-80"] += 1
        else:
            distribution_ranges["81-100"] += 1

    exam_score_buckets = {}
    for attempt in attempts:
        exam_score_buckets.setdefault(attempt.question_set_id, []).append(float(attempt.percentage or 0))

    avg_exam_labels, avg_exam_values = [], []
    for exam_id, scores in exam_score_buckets.items():
        exam = QuestionSet.query.get(exam_id)
        avg_exam_labels.append(exam.title if exam else f"Exam {exam_id}")
        avg_exam_values.append(round(sum(scores) / len(scores), 2) if scores else 0)

    taken_per_day = OrderedDict()
    for attempt in attempts:
        day_key = attempt.attempted_at.strftime("%Y-%m-%d")
        taken_per_day[day_key] = taken_per_day.get(day_key, 0) + 1

    chart_data = {
        "distribution_labels": list(distribution_ranges.keys()),
        "distribution_values": list(distribution_ranges.values()),
        "avg_exam_labels": avg_exam_labels,
        "avg_exam_values": avg_exam_values,
        "daily_labels": list(taken_per_day.keys()),
        "daily_values": list(taken_per_day.values()),
    }

    return render_template("admin/dashboard.html", stats=stats, recent_exams=recent_exams, chart_data=chart_data)


@bp.route("/exams", methods=["GET", "POST"], endpoint="admin_exams")
@login_required
@admin_required
def admin_exams():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        duration = request.form.get("duration", "60").strip()
        if not title:
            flash("Exam title is required.")
            return redirect(url_for("admin.admin_exams"))

        db.session.add(QuestionSet(title=title, description=description, duration=int(duration) if duration.isdigit() else 60, created_by=None))
        db.session.commit()
        flash("Exam created successfully.")
        return redirect(url_for("admin.admin_exams"))

    exams = QuestionSet.query.order_by(QuestionSet.created_at.desc()).all()
    return render_template("admin/exams.html", exams=exams)


@bp.post("/exams/<int:exam_id>/delete", endpoint="delete_exam")
@login_required
@admin_required
def delete_exam(exam_id: int):
    exam = QuestionSet.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted successfully.")
    return redirect(url_for("admin.admin_exams"))


@bp.route("/exams/<int:exam_id>/questions", methods=["GET", "POST"], endpoint="admin_questions")
@login_required
@admin_required
def admin_questions(exam_id: int):
    exam = QuestionSet.query.get_or_404(exam_id)

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        options = {
            "A": request.form.get("option_a", "").strip(),
            "B": request.form.get("option_b", "").strip(),
            "C": request.form.get("option_c", "").strip(),
            "D": request.form.get("option_d", "").strip(),
        }
        correct_answer = request.form.get("correct_answer", "").strip().upper()

        if not question_text or not all(options.values()) or correct_answer not in options:
            flash("All fields are required and correct answer must be A/B/C/D.")
            return redirect(url_for("admin.admin_questions", exam_id=exam.id))

        question = Question(question_set_id=exam.id, question_text=question_text)
        db.session.add(question)
        db.session.flush()

        for key, text in options.items():
            db.session.add(Option(question_id=question.id, option_text=text, is_correct=(key == correct_answer)))

        db.session.commit()
        flash("Question added successfully.")
        return redirect(url_for("admin.admin_questions", exam_id=exam.id))

    questions = Question.query.filter_by(question_set_id=exam.id).order_by(Question.id.desc()).all()
    return render_template("admin/questions.html", exam=exam, questions=questions)


@bp.post("/questions/<int:question_id>/delete", endpoint="delete_question")
@login_required
@admin_required
def delete_question(question_id: int):
    question = Question.query.get_or_404(question_id)
    exam_id = question.question_set_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.")
    return redirect(url_for("admin.admin_questions", exam_id=exam_id))


@bp.post("/questions/<int:question_id>/edit", endpoint="edit_question")
@login_required
@admin_required
def edit_question(question_id: int):
    flash("Edit is not available in legacy-compatible mode. Delete and recreate question.")
    question = Question.query.get_or_404(question_id)
    return redirect(url_for("admin.admin_questions", exam_id=question.question_set_id))

from collections import OrderedDict

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Exam, Question, Result, User, db
from app.routes.common import admin_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard", endpoint="admin_dashboard")
@login_required
@admin_required
def admin_dashboard():
    stats = {
        "total_students": User.query.filter_by(role="student").count(),
        "total_exams": Exam.query.count(),
        "total_questions": Question.query.count(),
        "total_results": Result.query.count(),
    }
    recent_exams = Exam.query.order_by(Exam.created_at.desc()).limit(5).all()

    results = Result.query.all()
    exams = Exam.query.all()
    exam_title_map = {exam.id: exam.title for exam in exams}

    distribution_ranges = OrderedDict([
        ("0-20", 0),
        ("21-40", 0),
        ("41-60", 0),
        ("61-80", 0),
        ("81-100", 0),
    ])
    for result in results:
        score = float(result.score or 0)
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
    for result in results:
        exam_score_buckets.setdefault(result.exam_id, []).append(float(result.score or 0))

    avg_exam_labels = []
    avg_exam_values = []
    for exam_id, scores in exam_score_buckets.items():
        avg_exam_labels.append(exam_title_map.get(exam_id, f"Exam {exam_id}"))
        avg_exam_values.append(round(sum(scores) / len(scores), 2) if scores else 0)

    taken_per_day = OrderedDict()
    for result in results:
        day_key = result.submitted_at.strftime("%Y-%m-%d") if result.submitted_at else "Unknown"
        taken_per_day[day_key] = taken_per_day.get(day_key, 0) + 1

    chart_data = {
        "distribution_labels": list(distribution_ranges.keys()),
        "distribution_values": list(distribution_ranges.values()),
        "avg_exam_labels": avg_exam_labels,
        "avg_exam_values": avg_exam_values,
        "daily_labels": list(taken_per_day.keys()),
        "daily_values": list(taken_per_day.values()),
    }

    return render_template(
        "admin/dashboard.html",
        stats=stats,
        recent_exams=recent_exams,
        chart_data=chart_data,
    )
    return render_template("admin/dashboard.html", stats=stats, recent_exams=recent_exams)


@bp.route("/exams", methods=["GET", "POST"], endpoint="admin_exams")
@login_required
@admin_required
def admin_exams():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        duration = request.form.get("duration", "60").strip()

        if not title:
            flash("Exam title is required.", "danger")
            return redirect(url_for("admin.admin_exams"))

        exam = Exam(
            title=title,
            description=description,
            duration=int(duration) if duration.isdigit() else 60,
        )
        db.session.add(exam)
        db.session.commit()
        flash("Exam created successfully.", "success")
        return redirect(url_for("admin.admin_exams"))

    exams = Exam.query.order_by(Exam.created_at.desc()).all()
    return render_template("admin/exams.html", exams=exams)


@bp.post("/exams/<int:exam_id>/delete", endpoint="delete_exam")
@login_required
@admin_required
def delete_exam(exam_id: int):
    exam = Exam.query.get_or_404(exam_id)
    db.session.delete(exam)
    db.session.commit()
    flash("Exam deleted successfully.", "success")
    return redirect(url_for("admin.admin_exams"))


@bp.route("/exams/<int:exam_id>/questions", methods=["GET", "POST"], endpoint="admin_questions")
@login_required
@admin_required
def admin_questions(exam_id: int):
    exam = Exam.query.get_or_404(exam_id)

    if request.method == "POST":
        question_text = request.form.get("question_text", "").strip()
        option_a = request.form.get("option_a", "").strip()
        option_b = request.form.get("option_b", "").strip()
        option_c = request.form.get("option_c", "").strip()
        option_d = request.form.get("option_d", "").strip()
        correct_answer = request.form.get("correct_answer", "").strip().upper()

        if not all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
            flash("All question fields are required.", "danger")
            return redirect(url_for("admin.admin_questions", exam_id=exam.id))

        if correct_answer not in {"A", "B", "C", "D"}:
            flash("Correct answer must be one of A, B, C, D.", "danger")
            return redirect(url_for("admin.admin_questions", exam_id=exam.id))

        question = Question(
            exam_id=exam.id,
            question_text=question_text,
            option_a=option_a,
            option_b=option_b,
            option_c=option_c,
            option_d=option_d,
            correct_answer=correct_answer,
        )
        db.session.add(question)
        db.session.commit()
        flash("Question added successfully.", "success")
        return redirect(url_for("admin.admin_questions", exam_id=exam.id))

    questions = Question.query.filter_by(exam_id=exam.id).order_by(Question.id.desc()).all()
    return render_template("admin/questions.html", exam=exam, questions=questions)


@bp.post("/questions/<int:question_id>/edit", endpoint="edit_question")
@login_required
@admin_required
def edit_question(question_id: int):
    question = Question.query.get_or_404(question_id)

    question.question_text = request.form.get("question_text", "").strip()
    question.option_a = request.form.get("option_a", "").strip()
    question.option_b = request.form.get("option_b", "").strip()
    question.option_c = request.form.get("option_c", "").strip()
    question.option_d = request.form.get("option_d", "").strip()
    question.correct_answer = request.form.get("correct_answer", "").strip().upper()

    if question.correct_answer not in {"A", "B", "C", "D"}:
        flash("Correct answer must be one of A, B, C, D.", "danger")
        return redirect(url_for("admin.admin_questions", exam_id=question.exam_id))

    db.session.commit()
    flash("Question updated.", "success")
    return redirect(url_for("admin.admin_questions", exam_id=question.exam_id))


@bp.post("/questions/<int:question_id>/delete", endpoint="delete_question")
@login_required
@admin_required
def delete_question(question_id: int):
    question = Question.query.get_or_404(question_id)
    exam_id = question.exam_id
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted.", "success")
    return redirect(url_for("admin.admin_questions", exam_id=exam_id))

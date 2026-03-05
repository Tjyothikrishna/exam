from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required

from app.models import Exam, Question, Result, User, db
from app.routes.common import admin_required
from flask import Blueprint, Response, redirect, render_template, url_for

from app.models import get_db_connection
from app.routes.common import admin_required
from app.services.admin_service import dashboard_stats

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
@admin_required
def admin_dashboard():
    stats = dashboard_stats()
    return render_template(
        "admin/dashboard.html",
        total_students=stats["total_students"],
        total_attempts=stats["total_attempts"],
        recent_attempts=stats["recent_attempts"],
        student_names=[],
        attempt_counts=[],
        passed_count=0,
        failed_count=0,
        attempt_days=[],
        attempt_trend=[],
    )


@bp.route("/students", endpoint="admin_students")
@admin_required
def admin_students():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT u.id, u.first_name, u.email, COUNT(ta.id) AS attempts, ROUND(AVG(ta.percentage),2) AS avg_score
        FROM users u
        LEFT JOIN test_attempts ta ON u.id = ta.user_id
        WHERE u.role='student'
        GROUP BY u.id
        """
    )
    students = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin/students.html", students=students)


@bp.route("/question_sets", endpoint="admin_question_sets")
@admin_required
def admin_question_sets():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM question_sets ORDER BY created_at DESC")
    sets = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("admin/question_sets.html", sets=sets)


@bp.route("/attempt/<int:attempt_id>", endpoint="admin_attempt_detail")
@admin_required
def admin_attempt_detail(attempt_id: int):
    return redirect(url_for("admin.admin_dashboard"))


@bp.route("/download_attempts_csv", endpoint="download_attempts_csv")
@admin_required
def download_attempts_csv():
    return Response("Student,Test,Score\n", mimetype="text/csv")

from flask import Blueprint, Response, redirect, render_template, url_for

from app.models import get_db_connection
from app.routes.common import admin_required
from app.services.admin_service import dashboard_stats

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/dashboard", endpoint="admin_dashboard")
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

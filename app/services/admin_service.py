from app.models import get_db_connection


def dashboard_stats():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total_students FROM users WHERE role='student'")
    total_students = cursor.fetchone()["total_students"]

    cursor.execute("SELECT COUNT(*) AS total_attempts FROM test_attempts")
    total_attempts = cursor.fetchone()["total_attempts"]

    cursor.execute(
        """
        SELECT ta.id, u.first_name, qs.title, ta.score, ta.percentage, ta.attempted_at
        FROM test_attempts ta
        JOIN users u ON ta.user_id = u.id
        JOIN question_sets qs ON ta.question_set_id = qs.id
        ORDER BY ta.attempted_at DESC LIMIT 10
        """
    )
    recent_attempts = cursor.fetchall()

    cursor.close()
    conn.close()

    return {
        "total_students": total_students,
        "total_attempts": total_attempts,
        "recent_attempts": recent_attempts,
    }

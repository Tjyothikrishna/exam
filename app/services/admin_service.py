from app.models import TestAttempt, User


def dashboard_stats():
    recent_attempts = (
        TestAttempt.query.order_by(TestAttempt.attempted_at.desc()).limit(10).all()
    )

    return {
        "total_students": User.query.filter_by(role="student").count(),
        "total_attempts": TestAttempt.query.count(),
        "recent_attempts": recent_attempts,
    }

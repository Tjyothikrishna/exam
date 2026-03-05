import random

from app.models import get_db_connection


def load_random_question_set():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT id, title FROM question_sets ORDER BY RAND() LIMIT 1")
    question_set = cursor.fetchone()
    if not question_set:
        cursor.close()
        conn.close()
        return [], None

    cursor.execute(
        "SELECT id, question_text FROM questions WHERE question_set_id = %s",
        (question_set["id"],),
    )
    questions = cursor.fetchall()

    for q in questions:
        cursor.execute(
            "SELECT id, option_text, is_correct FROM options WHERE question_id = %s",
            (q["id"],),
        )
        options = cursor.fetchall()
        q["options"] = options
        q["correct_option_id"] = next(
            (opt["id"] for opt in options if opt["is_correct"]),
            None,
        )

    cursor.close()
    conn.close()
    random.shuffle(questions)
    return questions, question_set["id"]


def save_attempt(user_id: int, question_set_id: int, questions: list, answers: list, score: int):
    total_questions = len(questions)
    percentage = round((score / total_questions) * 100, 2) if total_questions else 0
    passed = percentage >= 70

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO test_attempts
        (user_id, question_set_id, score, total_questions, percentage, passed)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (user_id, question_set_id, score, total_questions, percentage, passed),
    )
    attempt_id = cursor.lastrowid

    for ans in answers:
        cursor.execute(
            """
            INSERT INTO student_answers
            (test_attempt_id, question_id, selected_option_id, is_correct)
            VALUES (%s, %s, %s, %s)
            """,
            (
                attempt_id,
                ans["question_id"],
                ans["selected_option_id"],
                ans["is_correct"],
            ),
        )

    conn.commit()
    cursor.close()
    conn.close()

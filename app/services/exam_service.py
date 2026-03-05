import random

from app.models import QuestionSet, StudentAnswer, TestAttempt, db


def load_random_question_set():
    question_sets = QuestionSet.query.all()
    if not question_sets:
        return [], None

    question_set = random.choice(question_sets)
    questions_payload = []
    for question in question_set.questions:
        options = []
        correct_option_id = None
        for option in question.options:
            options.append({"id": option.id, "option_text": option.option_text})
            if option.is_correct:
                correct_option_id = option.id
        questions_payload.append(
            {
                "id": question.id,
                "question_text": question.question_text,
                "options": options,
                "correct_option_id": correct_option_id,
            }
        )

    random.shuffle(questions_payload)
    return questions_payload, question_set.id


def save_attempt(user_id: int, question_set_id: int, questions: list, answers: list, score: int):
    total_questions = len(questions)
    percentage = round((score / total_questions) * 100, 2) if total_questions else 0

    attempt = TestAttempt(
        user_id=user_id,
        question_set_id=question_set_id,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        passed=percentage >= 70,
    )
    db.session.add(attempt)
    db.session.flush()

    for ans in answers:
        db.session.add(
            StudentAnswer(
                test_attempt_id=attempt.id,
                question_id=ans["question_id"],
                selected_option_id=ans["selected_option_id"],
                is_correct=ans["is_correct"],
            )
        )

    db.session.commit()
    return attempt

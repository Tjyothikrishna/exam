import random
import smtplib
from email.mime.text import MIMEText

from flask import current_app
from werkzeug.security import check_password_hash, generate_password_hash

from app.models import get_db_connection


def generate_otp() -> int:
    return random.randint(100000, 999999)


def send_otp_email(recipient_email: str, otp: int) -> bool:
    email_user = current_app.config.get("EMAIL_USER")
    email_pass = current_app.config.get("EMAIL_PASS")
    if not email_user or not email_pass:
        return False

    try:
        msg = MIMEText(f"Your OTP for verification is: {otp}")
        msg["Subject"] = "OTP Verification"
        msg["From"] = email_user
        msg["To"] = recipient_email

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, recipient_email, msg.as_string())
        return True
    except Exception:
        return False


def create_student(signup_data: dict) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO users
            (first_name, last_name, email, mobile_number, password_hash, gender, profile_picture, role)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 'student')
            """,
            (
                signup_data["first_name"],
                signup_data["last_name"],
                signup_data["email"],
                signup_data["mobile_number"],
                signup_data["password_hash"],
                signup_data["gender"],
                signup_data["profile_picture"],
            ),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()


def find_user_by_email(email: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def validate_login(email: str, password: str):
    user = find_user_by_email(email)
    if user and check_password_hash(user["password_hash"], password):
        return user
    return None


def update_password(email: str, password: str) -> None:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE users SET password_hash = %s WHERE email = %s",
        (generate_password_hash(password), email),
    )
    conn.commit()
    cursor.close()
    conn.close()

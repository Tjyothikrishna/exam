import random
import smtplib
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText

from flask import current_app

from app.extensions import bcrypt
from app.models import User, db


def generate_otp() -> int:
    return random.randint(100000, 999999)


def otp_expiry(minutes: int = 10) -> str:
    return (datetime.now(timezone.utc) + timedelta(minutes=minutes)).isoformat()


def is_otp_expired(iso_value: str) -> bool:
    try:
        return datetime.now(timezone.utc) > datetime.fromisoformat(iso_value)
    except ValueError:
        return True


def send_otp_email(recipient_email: str, otp: int, purpose: str = "verification") -> bool:
    email_user = current_app.config.get("EMAIL_USER")
    email_pass = current_app.config.get("EMAIL_PASS")
    if not email_user or not email_pass:
        return False

    msg = MIMEText(f"Your OTP for {purpose} is: {otp}. This OTP expires in 10 minutes.")
    msg["Subject"] = f"Exam Portal {purpose.title()} OTP"
    msg["From"] = email_user
    msg["To"] = recipient_email

    try:
        with smtplib.SMTP(current_app.config.get("SMTP_HOST"), current_app.config.get("SMTP_PORT")) as server:
            server.starttls()
            server.login(email_user, email_pass)
            server.sendmail(email_user, recipient_email, msg.as_string())
        return True
    except Exception:
        return False


def create_student(signup_data: dict) -> User:
    user = User(
        first_name=signup_data["first_name"],
        last_name=signup_data["last_name"],
        email=signup_data["email"],
        mobile_number=signup_data.get("mobile_number"),
        password_hash=bcrypt.generate_password_hash(signup_data["password"]).decode("utf-8"),
        gender=signup_data.get("gender"),
        profile_picture=signup_data.get("profile_picture"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


def find_user_by_email(email: str):
    return User.query.filter_by(email=email.lower().strip()).first()


def validate_login(email: str, password: str):
    user = find_user_by_email(email)
    if user and bcrypt.check_password_hash(user.password_hash, password):
        return user
    return None


def update_password(email: str, password: str) -> None:
    user = find_user_by_email(email)
    if not user:
        return
    user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
    db.session.commit()

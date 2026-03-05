import os

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from app.services.auth_service import (
    create_student,
    find_user_by_email,
    generate_otp,
    send_otp_email,
    update_password,
    validate_login,
)

bp = Blueprint("auth", __name__)


def allowed_file(filename):
    allowed_extensions = {"png", "jpg", "jpeg", "gif"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


@bp.route("/", endpoint="index")
def index():
    return redirect(url_for("signup"))


@bp.route("/signup", methods=["GET", "POST"], endpoint="signup")
def signup():
    if request.method == "POST":
        signup_data = {
            "first_name": request.form["first_name"],
            "last_name": request.form["last_name"],
            "email": request.form["email"],
            "mobile_number": request.form["mobile_number"],
            "password_hash": generate_password_hash(request.form["password"]),
            "gender": request.form.get("gender"),
            "profile_picture": "static/images/profile_pictures/default_profile.png",
        }

        profile_pic = request.files.get("profile_pic")
        if profile_pic and allowed_file(profile_pic.filename):
            picture_path = os.path.join(
                "static/images/profile_pictures", f"{signup_data['email']}.jpg"
            )
            profile_pic.save(picture_path)
            signup_data["profile_picture"] = picture_path

        otp = generate_otp()
        if send_otp_email(signup_data["email"], otp):
            session["otp"] = otp
            session["signup_data"] = signup_data
            flash("OTP sent to your email.", "info")
            return redirect(url_for("verify_otp"))

        flash("Failed to send OTP. Configure EMAIL_USER/EMAIL_PASS.", "danger")

    return render_template("signup.html")


@bp.route("/verify_otp", methods=["GET", "POST"], endpoint="verify_otp")
def verify_otp():
    if request.method == "POST":
        otp = request.form["otp"]
        if str(session.get("otp")) == otp and session.get("signup_data"):
            if create_student(session.pop("signup_data")):
                session.pop("otp", None)
                flash("You have successfully signed up!", "success")
                return redirect(url_for("login"))
            flash("Signup failed. Email may already exist.", "danger")
        else:
            flash("Invalid OTP.", "danger")

    return render_template("verify_otp.html")


@bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if request.method == "POST":
        user = validate_login(request.form["email"], request.form["password"])
        if user:
            session.clear()
            session["user_id"] = user["id"]
            session["user_name"] = user["first_name"]
            session["role"] = user["role"]
            if user["role"] == "admin":
                return redirect(url_for("admin_dashboard"))
            return redirect(url_for("home"))
        flash("Invalid email or password", "danger")

    return render_template("login.html")


@bp.route("/forgot_password", methods=["GET", "POST"], endpoint="forgot_password")
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        if find_user_by_email(email):
            otp = generate_otp()
            if send_otp_email(email, otp):
                session["otp"] = otp
                session["email"] = email
                return redirect(url_for("reset_password"))
        flash("Could not process request.", "danger")
    return render_template("forgot_password.html")


@bp.route("/reset_password", methods=["GET", "POST"], endpoint="reset_password")
def reset_password():
    if request.method == "POST":
        otp = request.form["otp"]
        new_password = request.form["new_password"]
        confirm_password = request.form["confirm_password"]

        if str(session.get("otp")) != otp:
            flash("Invalid OTP", "danger")
            return redirect(url_for("reset_password"))
        if new_password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for("reset_password"))

        email = session.get("email")
        if email:
            update_password(email, new_password)
            session.pop("otp", None)
            session.pop("email", None)
            flash("Password updated successfully!", "success")
            return redirect(url_for("login"))

    return render_template("reset_password.html")


@bp.route("/logout", endpoint="logout")
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for("login"))

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from app.services.auth_service import (
    create_student,
    find_user_by_email,
    generate_otp,
    is_otp_expired,
    otp_expiry,
    send_otp_email,
    update_password,
    validate_login,
)

bp = Blueprint("auth", __name__)


@bp.route("/signup", methods=["GET", "POST"], endpoint="signup")
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("student.home"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        if password != confirm_password:
            flash("Passwords do not match.")
            return render_template("signup.html")

        if find_user_by_email(email):
            flash("Email already registered.")
            return render_template("signup.html")

        otp = generate_otp()
        signup_data = {
            "first_name": request.form.get("first_name", "").strip(),
            "last_name": request.form.get("last_name", "").strip(),
            "email": email,
            "mobile_number": request.form.get("mobile_number", "").strip(),
            "password": password,
            "gender": request.form.get("gender", "").strip(),
            "profile_picture": "static/images/profile_pictures/default_profile.png",
        }

        session["signup_otp"] = str(otp)
        session["signup_otp_expiry"] = otp_expiry()
        session["signup_data"] = signup_data

        if not send_otp_email(email, otp, purpose="signup verification"):
            flash("Failed to send OTP email. Check EMAIL_USER/EMAIL_PASS in .env.")
            return render_template("signup.html")

        flash("OTP sent to your email.")
        return redirect(url_for("auth.verify_otp"))

    return render_template("signup.html")


@bp.route("/verify_otp", methods=["GET", "POST"], endpoint="verify_otp")
def verify_otp():
    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        stored_otp = session.get("signup_otp")
        expiry = session.get("signup_otp_expiry", "")

        if not stored_otp:
            flash("Signup session expired. Please sign up again.")
            return redirect(url_for("auth.signup"))

        if is_otp_expired(expiry):
            flash("OTP expired. Please sign up again.")
            return redirect(url_for("auth.signup"))

        if entered_otp != stored_otp:
            flash("Invalid OTP.")
            return render_template("verify_otp.html")

        signup_data = session.get("signup_data")
        if not signup_data:
            flash("Signup session expired. Please try again.")
            return redirect(url_for("auth.signup"))

        create_student(signup_data)
        for key in ["signup_otp", "signup_otp_expiry", "signup_data"]:
            session.pop(key, None)

        flash("Account created successfully. Please login.")
        return redirect(url_for("auth.login"))

    return render_template("verify_otp.html")

    return render_template("verify_otp.html")

@bp.route("/login", methods=["GET", "POST"], endpoint="login")
def login():
    if current_user.is_authenticated:
        return redirect(url_for("student.home"))

    if request.method == "POST":
        user = validate_login(request.form.get("email", ""), request.form.get("password", ""))
        if not user:
            flash("Invalid email or password.")
            return render_template("login.html")

        login_user(user)
        if user.role == "admin":
            return redirect(url_for("admin.admin_dashboard"))
        return redirect(url_for("student.home"))

    return render_template("login.html")


@bp.route("/forgot_password", methods=["GET", "POST"], endpoint="forgot_password")
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = find_user_by_email(email)
        if not user:
            flash("No account found with that email.")
            return render_template("forgot_password.html")

        otp = generate_otp()
        session["reset_email"] = email
        session["reset_otp"] = str(otp)
        session["reset_otp_expiry"] = otp_expiry()

        if not send_otp_email(email, otp, purpose="password reset"):
            flash("Failed to send OTP email. Check EMAIL_USER/EMAIL_PASS in .env.")
            return render_template("forgot_password.html")

        flash("OTP sent to your email.")
        return redirect(url_for("auth.reset_password"))

    return render_template("forgot_password.html")


@bp.route("/reset_password", methods=["GET", "POST"], endpoint="reset_password")
def reset_password():
    if request.method == "POST":
        entered_otp = request.form.get("otp", "").strip()
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")

        if new_password != confirm_password:
            flash("Passwords do not match.")
            return render_template("reset_password.html")

        if is_otp_expired(session.get("reset_otp_expiry", "")):
            flash("OTP expired. Please retry forgot password flow.")
            return redirect(url_for("auth.forgot_password"))

        if entered_otp != session.get("reset_otp"):
            flash("Invalid OTP.")
            return render_template("reset_password.html")

        email = session.get("reset_email")
        if not email:
            flash("Session expired.")
            return redirect(url_for("auth.forgot_password"))

        update_password(email, new_password)
        for key in ["reset_email", "reset_otp", "reset_otp_expiry"]:
            session.pop(key, None)

        flash("Password reset successful. Please login.")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")


@bp.route("/logout", endpoint="logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.")
    return redirect(url_for("auth.login"))

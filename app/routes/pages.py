from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from app.models import db

bp = Blueprint("pages", __name__)


@bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("home"))
    return redirect(url_for("login"))


@bp.route("/about", endpoint="about")
def about():
    return render_template("about.html")


@bp.route("/help", methods=["GET", "POST"], endpoint="help")
def help_page():
    if request.method == "POST":
        flash("Help request submitted successfully.")
    return render_template("help.html")


@bp.route("/settings", methods=["GET", "POST"], endpoint="settings")
@login_required
def settings():
    if request.method == "POST":
        current_user.first_name = request.form.get("first_name", current_user.first_name)
        current_user.last_name = request.form.get("last_name", current_user.last_name)
        current_user.email = request.form.get("email", current_user.email).strip().lower()
        current_user.mobile_number = request.form.get("mobile", current_user.mobile_number)
        current_user.gender = request.form.get("gender", current_user.gender)
        db.session.commit()
        flash("Profile updated successfully.")
        return redirect(url_for("settings"))

    return render_template("settings.html", user=current_user)

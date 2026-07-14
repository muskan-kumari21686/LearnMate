"""Auth routes — login, register, logout."""

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from models import User, db

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    return render_template("index.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()

        if User.query.filter_by(username=username).first():
            flash("Username already taken.", "danger")
            return render_template("register.html")
        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "danger")
            return render_template("register.html")

        user = User(username=username, email=email, full_name=full_name)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        login_user(user)
        flash("Welcome to LearnMate! Let's set up your profile.", "success")
        return redirect(url_for("profile.setup"))
    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user, remember=True)
            # Update streak
            _update_streak(user)
            flash(f"Welcome back, {user.full_name or user.username}! 🎉", "success")
            return redirect(url_for("dashboard.dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.index"))


def _update_streak(user: User):
    """Increment streak if user was active yesterday, else reset."""
    from datetime import datetime, timedelta

    now = datetime.utcnow()
    if user.last_active:
        delta = (now.date() - user.last_active.date()).days
        if delta == 1:
            user.streak_days += 1
        elif delta > 1:
            user.streak_days = 1
        # delta == 0 → same day, no change
    else:
        user.streak_days = 1
    user.last_active = now
    db.session.commit()

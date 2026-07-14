"""Profile routes — view and edit user profile, setup wizard."""

from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import current_user, login_required

from models import db

profile_bp = Blueprint("profile", __name__)

CAREER_GOALS = [
    "Full-Stack Developer", "Data Scientist", "Machine Learning Engineer",
    "DevOps Engineer", "Cloud Architect", "Cybersecurity Analyst",
    "UI/UX Designer", "Product Manager", "Mobile Developer",
    "Blockchain Developer", "Game Developer", "AI Research Scientist",
    "Data Engineer", "Backend Developer", "Frontend Developer",
]

LEARNING_STYLES = [
    ("visual", "Visual — Learn best through diagrams, videos, and infographics"),
    ("reading", "Reading/Writing — Prefer books, articles, and note-taking"),
    ("hands-on", "Hands-on — Learn by doing projects and coding challenges"),
    ("mixed", "Mixed — Combination of all styles"),
]

SKILL_LEVELS = [
    ("beginner", "Beginner — I'm just starting out"),
    ("intermediate", "Intermediate — I have some experience"),
    ("advanced", "Advanced — I'm highly experienced"),
]


@profile_bp.route("/profile")
@login_required
def profile():
    return render_template(
        "profile.html",
        career_goals=CAREER_GOALS,
        learning_styles=LEARNING_STYLES,
        skill_levels=SKILL_LEVELS,
    )


@profile_bp.route("/profile/setup", methods=["GET", "POST"])
@login_required
def setup():
    if request.method == "POST":
        current_user.full_name = request.form.get("full_name", current_user.full_name)
        current_user.career_goal = request.form.get("career_goal", "")
        current_user.current_role = request.form.get("current_role", "")
        current_user.skill_level = request.form.get("skill_level", "beginner")
        current_user.learning_style = request.form.get("learning_style", "mixed")
        current_user.interests = request.form.get("interests", "")
        current_user.bio = request.form.get("bio", "")
        db.session.commit()
        flash("Profile updated! Your personalised learning journey begins now. 🚀", "success")
        return redirect(url_for("dashboard.dashboard"))
    return render_template(
        "setup.html",
        career_goals=CAREER_GOALS,
        learning_styles=LEARNING_STYLES,
        skill_levels=SKILL_LEVELS,
    )


@profile_bp.route("/profile/update", methods=["POST"])
@login_required
def update():
    data = request.get_json(silent=True) or request.form
    fields = ["full_name", "career_goal", "current_role", "skill_level", "learning_style", "interests", "bio"]
    for field in fields:
        value = data.get(field)
        if value is not None:
            setattr(current_user, field, value)
    db.session.commit()
    return jsonify({"status": "updated"})

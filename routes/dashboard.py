"""Dashboard routes."""

from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from models import Course, CourseProgress, db

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard")
@login_required
def dashboard():
    # Stats
    completed = len(current_user.completed_courses)
    in_progress = len(current_user.in_progress_courses)
    total_enrolled = len(current_user.progress)

    # Recent activity (last 5 in-progress or completed)
    recent = (
        CourseProgress.query
        .filter_by(user_id=current_user.id)
        .filter(CourseProgress.status.in_(["in_progress", "completed"]))
        .order_by(CourseProgress.started_at.desc())
        .limit(5)
        .all()
    )

    # Recommended courses (not yet enrolled, matching domain)
    enrolled_ids = [p.course_id for p in current_user.progress]
    recommended = (
        Course.query
        .filter(Course.id.notin_(enrolled_ids))
        .filter_by(level=current_user.skill_level or "beginner")
        .limit(6)
        .all()
    )
    if len(recommended) < 3:
        recommended = Course.query.filter(Course.id.notin_(enrolled_ids)).limit(6).all()

    # XP milestone
    xp = current_user.total_xp
    next_milestone = _next_xp_milestone(xp)

    return render_template(
        "dashboard.html",
        completed=completed,
        in_progress=in_progress,
        total_enrolled=total_enrolled,
        recent=recent,
        recommended=recommended,
        xp=xp,
        next_milestone=next_milestone,
    )


def _next_xp_milestone(xp: int) -> dict:
    milestones = [
        (500, "Explorer"),
        (1500, "Learner"),
        (3000, "Achiever"),
        (6000, "Master"),
        (10000, "Legend"),
    ]
    for threshold, badge in milestones:
        if xp < threshold:
            pct = round((xp / threshold) * 100)
            return {"threshold": threshold, "badge": badge, "pct": min(pct, 100)}
    return {"threshold": 10000, "badge": "Legend", "pct": 100}

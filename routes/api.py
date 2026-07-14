"""API routes — JSON endpoints for the frontend."""

from flask import Blueprint, jsonify, request
from flask_login import current_user, login_required

from models import Course, CourseProgress, db

api_bp = Blueprint("api", __name__)


@api_bp.route("/stats")
@login_required
def stats():
    completed = len(current_user.completed_courses)
    in_progress = len(current_user.in_progress_courses)
    total_hours = sum(
        (p.course.duration_hours or 0) * (p.progress_pct / 100)
        for p in current_user.progress
        if p.course
    )
    return jsonify({
        "completed_courses": completed,
        "in_progress_courses": in_progress,
        "total_xp": current_user.total_xp,
        "streak_days": current_user.streak_days,
        "level_badge": current_user.level_badge,
        "total_hours_learned": round(total_hours, 1),
    })


@api_bp.route("/courses/search")
@login_required
def search_courses():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"courses": []})
    results = (
        Course.query
        .filter(Course.title.ilike(f"%{q}%") | Course.tags.ilike(f"%{q}%") | Course.domain.ilike(f"%{q}%"))
        .limit(10)
        .all()
    )
    return jsonify({"courses": [c.to_dict() for c in results]})


@api_bp.route("/user/progress")
@login_required
def user_progress():
    progress = [p.to_dict() for p in current_user.progress]
    return jsonify({"progress": progress})

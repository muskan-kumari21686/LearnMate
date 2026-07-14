"""Courses routes — browse, search, enroll, and track progress."""

from flask import Blueprint, jsonify, render_template, request, redirect, url_for, flash
from flask_login import current_user, login_required
from datetime import datetime

from models import Course, CourseProgress, User, db

courses_bp = Blueprint("courses", __name__)


@courses_bp.route("/courses")
@login_required
def courses():
    query = request.args.get("q", "").strip()
    domain = request.args.get("domain", "")
    level = request.args.get("level", "")

    q = Course.query
    if query:
        q = q.filter(Course.title.ilike(f"%{query}%") | Course.tags.ilike(f"%{query}%"))
    if domain:
        q = q.filter_by(domain=domain)
    if level:
        q = q.filter_by(level=level)

    all_courses = q.order_by(Course.rating.desc()).all()

    # Determine enrollment status for each course
    enrolled_map = {p.course_id: p for p in current_user.progress}

    domains = sorted(set(c.domain for c in Course.query.all() if c.domain))
    return render_template(
        "courses.html",
        courses=all_courses,
        enrolled_map=enrolled_map,
        domains=domains,
        query=query,
        selected_domain=domain,
        selected_level=level,
    )


@courses_bp.route("/courses/<int:course_id>/enroll", methods=["POST"])
@login_required
def enroll(course_id: int):
    course = Course.query.get_or_404(course_id)
    existing = CourseProgress.query.filter_by(user_id=current_user.id, course_id=course_id).first()
    if existing:
        return jsonify({"status": "already_enrolled"})

    progress = CourseProgress(
        user_id=current_user.id,
        course_id=course_id,
        status="in_progress",
        progress_pct=0,
        started_at=datetime.utcnow(),
    )
    db.session.add(progress)
    course.enrollments = (course.enrollments or 0) + 1
    db.session.commit()
    return jsonify({"status": "enrolled", "course_title": course.title})


@courses_bp.route("/courses/<int:course_id>/unenroll", methods=["POST"])
@login_required
def unenroll(course_id: int):
    progress = CourseProgress.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first()
    if not progress:
        return jsonify({"status": "not_enrolled"})
    # Deduct XP if the course was completed
    if progress.status == "completed":
        course = Course.query.get(course_id)
        xp_deduct = course.xp_reward if course else 100
        current_user.total_xp = max(0, (current_user.total_xp or 0) - xp_deduct)
        # Decrement enrollment count
        if course and course.enrollments:
            course.enrollments = max(0, course.enrollments - 1)
    else:
        course = Course.query.get(course_id)
        if course and course.enrollments:
            course.enrollments = max(0, course.enrollments - 1)
    db.session.delete(progress)
    db.session.commit()
    return jsonify({"status": "unenrolled"})


@courses_bp.route("/courses/<int:course_id>/progress", methods=["POST"])
@login_required
def update_progress(course_id: int):
    progress = CourseProgress.query.filter_by(
        user_id=current_user.id, course_id=course_id
    ).first_or_404()
    data = request.get_json(silent=True) or {}
    new_pct = int(data.get("progress_pct", progress.progress_pct))
    new_pct = max(0, min(100, new_pct))
    progress.progress_pct = new_pct

    if new_pct == 100 and progress.status != "completed":
        progress.status = "completed"
        progress.completed_at = datetime.utcnow()
        # Award XP
        course = Course.query.get(course_id)
        xp_award = course.xp_reward if course else 100
        current_user.total_xp = (current_user.total_xp or 0) + xp_award
        db.session.commit()
        return jsonify({"status": "completed", "xp_awarded": xp_award})

    db.session.commit()
    return jsonify({"status": "updated", "progress_pct": new_pct})


@courses_bp.route("/courses/recommendations")
@login_required
def ai_recommendations():
    topic = request.args.get("topic", "")
    recommendations = agent.recommend_courses(current_user.to_dict(), topic or None)
    return jsonify({"recommendations": recommendations})


# Import here to avoid circular import
from agent import agent  # noqa: E402

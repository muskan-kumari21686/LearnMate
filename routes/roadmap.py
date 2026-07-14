"""Roadmap routes — generate and display personalised learning roadmap."""

import json

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required
from datetime import datetime

from agent import agent
from models import LearningRoadmap, db

roadmap_bp = Blueprint("roadmap", __name__)


@roadmap_bp.route("/roadmap")
@login_required
def roadmap():
    active_roadmap = (
        LearningRoadmap.query
        .filter_by(user_id=current_user.id, is_active=True)
        .order_by(LearningRoadmap.created_at.desc())
        .first()
    )
    roadmap_data = None
    if active_roadmap:
        try:
            roadmap_data = json.loads(active_roadmap.content)
        except (json.JSONDecodeError, TypeError):
            roadmap_data = None

    return render_template("roadmap.html", roadmap=roadmap_data, roadmap_record=active_roadmap)


@roadmap_bp.route("/roadmap/generate", methods=["POST"])
@login_required
def generate():
    data = request.get_json(silent=True) or {}
    career_goal = data.get("career_goal") or current_user.career_goal or "Software Developer"
    skill_level = data.get("skill_level") or current_user.skill_level or "beginner"
    interests = data.get("interests") or current_user.interests or "programming"

    roadmap_data = agent.generate_roadmap(career_goal, skill_level, interests, current_user.to_dict())

    # Deactivate previous roadmaps
    LearningRoadmap.query.filter_by(user_id=current_user.id, is_active=True).update({"is_active": False})

    new_roadmap = LearningRoadmap(
        user_id=current_user.id,
        title=roadmap_data.get("title", f"Roadmap for {career_goal}"),
        career_goal=career_goal,
        content=json.dumps(roadmap_data),
        is_active=True,
    )
    db.session.add(new_roadmap)
    db.session.commit()

    return jsonify({"roadmap": roadmap_data, "id": new_roadmap.id})


@roadmap_bp.route("/roadmap/history")
@login_required
def history():
    roadmaps = (
        LearningRoadmap.query
        .filter_by(user_id=current_user.id)
        .order_by(LearningRoadmap.created_at.desc())
        .limit(10)
        .all()
    )
    return jsonify({"roadmaps": [r.to_dict() for r in roadmaps]})

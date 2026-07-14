"""
LearnMate — Flask Application
Main application factory, routes, and API endpoints.
"""

import json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import (Flask, flash, jsonify, redirect, render_template, request,
                   session, url_for)
from flask_login import (LoginManager, current_user, login_required,
                         login_user, logout_user)
from flask_wtf.csrf import CSRFProtect

from agent import agent
from models import (ChatHistory, Course, CourseProgress, LearningRoadmap,
                    SkillAssessment, User, db)

load_dotenv()

# ─────────────────────────────────────────────────────────────────────────────
# Application factory
# ─────────────────────────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)

    # Core config
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-change-me")
    app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///learnmate.db")
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["WTF_CSRF_ENABLED"] = True

    # Extensions
    db.init_app(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"

    @login_manager.user_loader
    def load_user(user_id: str):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.chat import chat_bp
    from routes.courses import courses_bp
    from routes.roadmap import roadmap_bp
    from routes.assessment import assessment_bp
    from routes.profile import profile_bp
    from routes.api import api_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(chat_bp)
    app.register_blueprint(courses_bp)
    app.register_blueprint(roadmap_bp)
    app.register_blueprint(assessment_bp)
    app.register_blueprint(profile_bp)
    app.register_blueprint(api_bp, url_prefix="/api")

    # DB init + seed
    with app.app_context():
        db.create_all()
        _seed_sample_data()

    return app


# ─────────────────────────────────────────────────────────────────────────────
# Sample-data seeder
# ─────────────────────────────────────────────────────────────────────────────

def _seed_sample_data():
    """Seed the DB with sample courses if it is empty."""
    if Course.query.first():
        return
    try:
        from sample_data import SAMPLE_COURSES
        for c in SAMPLE_COURSES:
            db.session.add(Course(**c))
        db.session.commit()
        print(f"[LearnMate] Seeded {len(SAMPLE_COURSES)} sample courses.")
    except Exception as exc:  # noqa: BLE001
        print(f"[LearnMate] Seed error: {exc}")
        db.session.rollback()


# ─────────────────────────────────────────────────────────────────────────────
# Run
# ─────────────────────────────────────────────────────────────────────────────

app = create_app()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)

"""
LearnMate — Database Models
SQLAlchemy ORM models for User, Course, Progress, ChatHistory,
SkillAssessment, and LearningRoadmap.
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# ─────────────────────────────────────────────────────────────────────────────
# User
# ─────────────────────────────────────────────────────────────────────────────
class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(150), nullable=True)
    avatar_url = db.Column(db.String(300), nullable=True)

    # Profile details
    career_goal = db.Column(db.String(200), nullable=True)
    current_role = db.Column(db.String(150), nullable=True)
    skill_level = db.Column(db.String(50), default="beginner")   # beginner / intermediate / advanced
    learning_style = db.Column(db.String(80), nullable=True)     # visual / reading / hands-on / mixed
    interests = db.Column(db.Text, nullable=True)                # comma-separated tags
    bio = db.Column(db.Text, nullable=True)
    total_xp = db.Column(db.Integer, default=0)
    streak_days = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    progress = db.relationship("CourseProgress", back_populates="user", cascade="all, delete-orphan")
    chat_history = db.relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")
    assessments = db.relationship("SkillAssessment", back_populates="user", cascade="all, delete-orphan")
    roadmaps = db.relationship("LearningRoadmap", back_populates="user", cascade="all, delete-orphan")

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def completed_courses(self):
        return [p for p in self.progress if p.status == "completed"]

    @property
    def in_progress_courses(self):
        return [p for p in self.progress if p.status == "in_progress"]

    @property
    def level_badge(self) -> str:
        if self.total_xp < 500:
            return "Newcomer"
        elif self.total_xp < 1500:
            return "Explorer"
        elif self.total_xp < 3000:
            return "Learner"
        elif self.total_xp < 6000:
            return "Achiever"
        else:
            return "Master"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "career_goal": self.career_goal,
            "skill_level": self.skill_level,
            "learning_style": self.learning_style,
            "interests": self.interests,
            "total_xp": self.total_xp,
            "streak_days": self.streak_days,
            "level_badge": self.level_badge,
        }

    def __repr__(self):
        return f"<User {self.username}>"


# ─────────────────────────────────────────────────────────────────────────────
# Course
# ─────────────────────────────────────────────────────────────────────────────
class Course(db.Model):
    __tablename__ = "courses"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(100), nullable=True)
    domain = db.Column(db.String(100), nullable=True)
    level = db.Column(db.String(50), default="beginner")         # beginner / intermediate / advanced
    duration_hours = db.Column(db.Float, default=0.0)
    xp_reward = db.Column(db.Integer, default=100)
    provider = db.Column(db.String(150), nullable=True)
    url = db.Column(db.String(500), nullable=True)
    thumbnail = db.Column(db.String(500), nullable=True)
    tags = db.Column(db.Text, nullable=True)                     # comma-separated
    prerequisites = db.Column(db.Text, nullable=True)            # comma-separated course IDs or names
    rating = db.Column(db.Float, default=4.0)
    enrollments = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    progress = db.relationship("CourseProgress", back_populates="course", cascade="all, delete-orphan")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "domain": self.domain,
            "level": self.level,
            "duration_hours": self.duration_hours,
            "xp_reward": self.xp_reward,
            "provider": self.provider,
            "url": self.url,
            "tags": self.tags,
            "prerequisites": self.prerequisites,
            "rating": self.rating,
            "enrollments": self.enrollments,
        }

    def __repr__(self):
        return f"<Course {self.title}>"


# ─────────────────────────────────────────────────────────────────────────────
# CourseProgress
# ─────────────────────────────────────────────────────────────────────────────
class CourseProgress(db.Model):
    __tablename__ = "course_progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey("courses.id"), nullable=False)
    status = db.Column(db.String(30), default="not_started")     # not_started / in_progress / completed
    progress_pct = db.Column(db.Integer, default=0)              # 0 – 100
    score = db.Column(db.Float, nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    # Relationships
    user = db.relationship("User", back_populates="progress")
    course = db.relationship("Course", back_populates="progress")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "course": self.course.to_dict() if self.course else None,
            "status": self.status,
            "progress_pct": self.progress_pct,
            "score": self.score,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }

    def __repr__(self):
        return f"<CourseProgress user={self.user_id} course={self.course_id} {self.status}>"


# ─────────────────────────────────────────────────────────────────────────────
# ChatHistory
# ─────────────────────────────────────────────────────────────────────────────
class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    role = db.Column(db.String(20), nullable=False)              # user / assistant
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", back_populates="chat_history")

    def to_dict(self) -> dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self):
        return f"<ChatHistory user={self.user_id} role={self.role}>"


# ─────────────────────────────────────────────────────────────────────────────
# SkillAssessment
# ─────────────────────────────────────────────────────────────────────────────
class SkillAssessment(db.Model):
    __tablename__ = "skill_assessments"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    domain = db.Column(db.String(100), nullable=False)
    skill_level = db.Column(db.String(50), nullable=False)       # beginner / intermediate / advanced
    score = db.Column(db.Float, nullable=True)
    feedback = db.Column(db.Text, nullable=True)
    taken_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    user = db.relationship("User", back_populates="assessments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "domain": self.domain,
            "skill_level": self.skill_level,
            "score": self.score,
            "feedback": self.feedback,
            "taken_at": self.taken_at.isoformat(),
        }

    def __repr__(self):
        return f"<SkillAssessment user={self.user_id} domain={self.domain}>"


# ─────────────────────────────────────────────────────────────────────────────
# LearningRoadmap
# ─────────────────────────────────────────────────────────────────────────────
class LearningRoadmap(db.Model):
    __tablename__ = "learning_roadmaps"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(250), nullable=False)
    career_goal = db.Column(db.String(250), nullable=True)
    content = db.Column(db.Text, nullable=False)                 # JSON string — stages array
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = db.relationship("User", back_populates="roadmaps")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "career_goal": self.career_goal,
            "content": self.content,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat(),
        }

    def __repr__(self):
        return f"<LearningRoadmap user={self.user_id} title={self.title}>"

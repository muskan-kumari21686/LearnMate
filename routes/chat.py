"""Chat routes — AI chatbot interface."""

from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user, login_required

from agent import agent, AGENT_INSTRUCTIONS
from models import ChatHistory, db

chat_bp = Blueprint("chat", __name__)


@chat_bp.route("/chat")
@login_required
def chat():
    # Load last 20 messages for display
    history = (
        ChatHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(ChatHistory.timestamp.asc())
        .limit(20)
        .all()
    )
    return render_template("chat.html", history=history, agent_name=AGENT_INSTRUCTIONS["identity"]["name"])


@chat_bp.route("/chat/send", methods=["POST"])
@login_required
def send_message():
    data = request.get_json(silent=True) or {}
    user_message = (data.get("message") or "").strip()
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Save user message
    db.session.add(ChatHistory(user_id=current_user.id, role="user", content=user_message))
    db.session.commit()

    # Build recent history for context
    recent = (
        ChatHistory.query
        .filter_by(user_id=current_user.id)
        .order_by(ChatHistory.timestamp.asc())
        .limit(16)
        .all()
    )
    history = [{"role": h.role, "content": h.content} for h in recent]

    # Generate AI response
    ai_reply = agent.chat(user_message, history, current_user.to_dict())

    # Save assistant message
    db.session.add(ChatHistory(user_id=current_user.id, role="assistant", content=ai_reply))
    db.session.commit()

    return jsonify({"reply": ai_reply})


@chat_bp.route("/chat/clear", methods=["POST"])
@login_required
def clear_chat():
    ChatHistory.query.filter_by(user_id=current_user.id).delete()
    db.session.commit()
    return jsonify({"status": "cleared"})

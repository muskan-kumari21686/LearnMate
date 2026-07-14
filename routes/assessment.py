"""Assessment routes — skill assessment quiz and feedback."""

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user, login_required

from agent import agent
from models import SkillAssessment, User, db

assessment_bp = Blueprint("assessment", __name__)

# Static quiz questions per domain
QUIZ_BANK = {
    "Python": [
        {"q": "What is the output of `print(type([]))`?", "options": ["<class 'list'>", "<class 'tuple'>", "<class 'dict'>", "<class 'array'>"], "answer": 0},
        {"q": "Which keyword is used to define a function in Python?", "options": ["func", "define", "def", "function"], "answer": 2},
        {"q": "What does `len([1, 2, 3])` return?", "options": ["2", "3", "4", "1"], "answer": 1},
        {"q": "Which of the following is immutable in Python?", "options": ["list", "dict", "set", "tuple"], "answer": 3},
        {"q": "What is the correct way to create a dictionary?", "options": ["d = []", "d = ()", "d = {}", "d = <>"], "answer": 2},
    ],
    "Machine Learning": [
        {"q": "What does 'supervised learning' mean?", "options": ["Learning without labels", "Learning with labelled data", "Learning by rewards", "Unsupervised clustering"], "answer": 1},
        {"q": "Which algorithm is used for classification?", "options": ["Linear Regression", "K-Means", "Random Forest", "PCA"], "answer": 2},
        {"q": "What is overfitting?", "options": ["Model underfits training data", "Model performs well on all data", "Model memorises training data but fails on new data", "Model ignores training data"], "answer": 2},
        {"q": "What is the purpose of a validation set?", "options": ["To train the model", "To tune hyperparameters", "To test final performance", "To clean data"], "answer": 1},
        {"q": "Which metric is used for regression problems?", "options": ["Accuracy", "F1 Score", "RMSE", "AUC-ROC"], "answer": 2},
    ],
    "Web Development": [
        {"q": "What does HTML stand for?", "options": ["Hyper Text Markup Language", "High Tech Modern Language", "Hyper Transfer Markup Language", "Home Tool Markup Language"], "answer": 0},
        {"q": "Which CSS property controls the text size?", "options": ["font-style", "text-size", "font-size", "text-weight"], "answer": 2},
        {"q": "What is the purpose of JavaScript in web development?", "options": ["Structure", "Styling", "Interactivity", "Server management"], "answer": 2},
        {"q": "What does REST stand for?", "options": ["Remote Execution State Transfer", "Representational State Transfer", "Remote State Transfer", "Resource Exchange State Transfer"], "answer": 1},
        {"q": "Which HTTP method is used to retrieve data?", "options": ["POST", "PUT", "DELETE", "GET"], "answer": 3},
    ],
    "Data Science": [
        {"q": "What is a DataFrame in Pandas?", "options": ["A 1D array", "A 2D labelled data structure", "A neural network layer", "A type of plot"], "answer": 1},
        {"q": "Which library is used for data visualisation in Python?", "options": ["NumPy", "SciPy", "Matplotlib", "TensorFlow"], "answer": 2},
        {"q": "What does EDA stand for?", "options": ["Exploratory Data Analysis", "Extended Data Architecture", "External Data Algorithm", "Efficient Data Aggregation"], "answer": 0},
        {"q": "What is the purpose of normalisation?", "options": ["Remove duplicates", "Scale features to a common range", "Increase dataset size", "Reduce model complexity"], "answer": 1},
        {"q": "What is a correlation coefficient?", "options": ["Measures prediction accuracy", "Measures linear relationship between variables", "Measures clustering quality", "Measures model loss"], "answer": 1},
    ],
    "Cloud Computing": [
        {"q": "What does IaaS stand for?", "options": ["Internet as a Service", "Infrastructure as a Service", "Integration as a Service", "Information as a Service"], "answer": 1},
        {"q": "Which AWS service is used for object storage?", "options": ["EC2", "RDS", "S3", "Lambda"], "answer": 2},
        {"q": "What is a VPC?", "options": ["Virtual Private Cloud", "Virtual Public Container", "Verified Private Connection", "Virtual Processing Core"], "answer": 0},
        {"q": "What is serverless computing?", "options": ["Computing without servers", "Running code without managing servers", "Offline computing", "Local computing"], "answer": 1},
        {"q": "Which cloud model is shared between public and private?", "options": ["Hybrid Cloud", "Community Cloud", "Multi Cloud", "Edge Cloud"], "answer": 0},
    ],
    "Cybersecurity": [
        {"q": "What does CIA stand for in cybersecurity?", "options": ["Control, Integrity, Access", "Confidentiality, Integrity, Availability", "Cyber Intelligence Agency", "Central Information Architecture"], "answer": 1},
        {"q": "What is a phishing attack?", "options": ["Physical server attack", "Social engineering via fake emails/sites", "DDoS attack", "SQL injection"], "answer": 1},
        {"q": "What does VPN stand for?", "options": ["Virtual Public Network", "Very Private Network", "Virtual Private Network", "Verified Protected Network"], "answer": 2},
        {"q": "What is two-factor authentication?", "options": ["Two passwords required", "Something you know + something you have", "Biometric only", "Double encryption"], "answer": 1},
        {"q": "What is SQL injection?", "options": ["Injecting SQL queries via user input to manipulate databases", "A database backup technique", "An SQL optimisation method", "A server configuration attack"], "answer": 0},
    ],
}


@assessment_bp.route("/assessment")
@login_required
def assessment():
    domains = list(QUIZ_BANK.keys())
    past = (
        SkillAssessment.query
        .filter_by(user_id=current_user.id)
        .order_by(SkillAssessment.taken_at.desc())
        .limit(5)
        .all()
    )
    return render_template("assessment.html", domains=domains, past_assessments=past)


@assessment_bp.route("/assessment/quiz/<domain>")
@login_required
def quiz(domain: str):
    questions = QUIZ_BANK.get(domain)
    if not questions:
        return {"error": "Domain not found"}, 404
    # Strip answers before sending to client
    safe_questions = [
        {"id": i, "q": item["q"], "options": item["options"]}
        for i, item in enumerate(questions)
    ]
    return jsonify({"domain": domain, "questions": safe_questions})


@assessment_bp.route("/assessment/submit", methods=["POST"])
@login_required
def submit():
    data = request.get_json(silent=True) or {}
    domain = data.get("domain", "")
    user_answers = data.get("answers", {})  # {question_index: chosen_option_index}

    questions = QUIZ_BANK.get(domain, [])
    if not questions:
        return jsonify({"error": "Invalid domain"}), 400

    results = []
    for i, q in enumerate(questions):
        user_choice = user_answers.get(str(i))
        correct = user_choice == q["answer"] if user_choice is not None else False
        results.append({
            "question": q["q"],
            "user_answer": q["options"][user_choice] if user_choice is not None else "Not answered",
            "correct_answer": q["options"][q["answer"]],
            "correct": correct,
        })

    assessment_result = agent.assess_skill(domain, results, current_user.to_dict())

    # Save assessment
    record = SkillAssessment(
        user_id=current_user.id,
        domain=domain,
        skill_level=assessment_result["level"],
        score=assessment_result["score"],
        feedback=assessment_result["feedback"],
    )
    db.session.add(record)

    # Update user skill level if this is their primary domain
    if not current_user.skill_level or current_user.skill_level == "beginner":
        current_user.skill_level = assessment_result["level"]

    # XP reward for taking assessment
    current_user.total_xp = (current_user.total_xp or 0) + 50
    db.session.commit()

    return jsonify({
        "score": assessment_result["score"],
        "level": assessment_result["level"],
        "feedback": assessment_result["feedback"],
        "results": results,
        "xp_awarded": 50,
    })

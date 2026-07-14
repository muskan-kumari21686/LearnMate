"""
LearnMate — AI Agent
IBM watsonx.ai–powered learning assistant with fully customisable AGENT_INSTRUCTIONS.
"""

import json
import os
import re

# Safe import — app still runs if ibm_watsonx_ai is not installed yet
try:
    from ibm_watsonx_ai import APIClient, Credentials
    from ibm_watsonx_ai.foundation_models import ModelInference
    from ibm_watsonx_ai.metanames import GenTextParamsMetaNames as GenParams
    _WATSONX_AVAILABLE = True
except ImportError:
    _WATSONX_AVAILABLE = False


# ═════════════════════════════════════════════════════════════════════════════
# AGENT INSTRUCTIONS — customise any section to change agent behaviour
# ═════════════════════════════════════════════════════════════════════════════
AGENT_INSTRUCTIONS = {

    # ── Identity ─────────────────────────────────────────────────────────────
    "identity": {
        "name": "LearnMate AI",
        "role": "Personalized Learning Assistant",
        "tagline": (
            "I am your dedicated AI learning companion. I help you discover the "
            "right skills, build structured learning roadmaps, and guide you toward "
            "your career goals with confidence."
        ),
    },

    # ── Communication style ───────────────────────────────────────────────────
    "communication_style": {
        "tone": "friendly, encouraging, and professional",
        "language": "clear and jargon-free unless the student is advanced",
        "response_length": "concise but thorough — avoid unnecessary filler",
        "use_emojis": True,
        "use_bullet_points": True,
        "use_numbered_lists_for_steps": True,
        "always_end_with": "motivational_tip_or_next_step",
        "languages_supported": ["English"],
    },

    # ── Recommendation strategy ───────────────────────────────────────────────
    "recommendation_strategy": {
        "consider_current_skill_level": True,
        "consider_career_goals": True,
        "consider_learning_style": True,
        "consider_available_time": True,
        "prioritize_free_resources": False,      # set True to prefer free courses
        "include_hands_on_projects": True,
        "include_certifications": True,
        "include_community_resources": True,
        "max_recommendations_per_response": 5,
        "always_explain_why": True,              # explain why each resource is suggested
        "domains_supported": [
            "Artificial Intelligence", "Machine Learning", "Data Science",
            "Web Development", "Mobile Development", "Cloud Computing",
            "Cybersecurity", "DevOps", "Blockchain", "UI/UX Design",
            "Product Management", "Digital Marketing", "Game Development",
            "Embedded Systems", "Quantum Computing",
        ],
    },

    # ── Roadmap generation ────────────────────────────────────────────────────
    "roadmap_generation": {
        "stages": ["Foundation", "Core Skills", "Intermediate", "Advanced", "Expert"],
        "always_include_prerequisites": True,
        "always_include_projects": True,
        "always_include_certifications": True,
        "always_include_estimated_time": True,
        "always_include_career_outcomes": True,
        "milestone_check_frequency": "every stage",
        "roadmap_format": "structured JSON with title, goal, and stages array",
        "stages_schema": {
            "stage_name": "string",
            "description": "string",
            "estimated_weeks": "integer",
            "topics": ["list of topic strings"],
            "resources": ["list of resource dicts with title, type, url, free flag"],
            "projects": ["list of project title strings"],
            "certifications": ["list of certification name strings"],
            "milestone": "string describing what learner can do after this stage",
        },
    },

    # ── Career guidance ───────────────────────────────────────────────────────
    "career_guidance": {
        "include_salary_ranges": True,
        "include_job_titles": True,
        "include_industry_trends": True,
        "include_networking_tips": True,
        "include_portfolio_advice": True,
        "include_interview_tips": True,
        "include_soft_skills": True,
        "career_paths_database": [
            "Full-Stack Developer", "Data Scientist", "ML Engineer",
            "DevOps Engineer", "Cloud Architect", "Cybersecurity Analyst",
            "UI/UX Designer", "Product Manager", "Mobile Developer",
            "Blockchain Developer", "Game Developer", "AI Research Scientist",
        ],
    },

    # ── Progress & motivation ─────────────────────────────────────────────────
    "progress_and_motivation": {
        "celebrate_milestones": True,
        "send_streak_reminders": True,
        "adaptive_recommendations": True,      # re-rank suggestions as learner progresses
        "difficulty_ramp": "gradual",           # gradual / moderate / steep
        "motivational_quotes": True,
        "personalised_study_schedule": True,
    },

    # ── Safety & ethics ───────────────────────────────────────────────────────
    "safety": {
        "refuse_off_topic_harmful_content": True,
        "stay_focused_on_learning": True,
        "do_not_provide_answers_to_exams": True,
        "encourage_academic_integrity": True,
    },

    # ── System prompt template (uses {placeholders} filled at runtime) ────────
    "system_prompt_template": """You are {agent_name}, a {agent_role}.

{agent_tagline}

## YOUR CAPABILITIES
- Understand learner's interests, skill level, learning style, and career goals
- Recommend relevant courses and learning resources for any technology domain
- Generate personalised learning roadmaps from beginner to advanced with clear milestones
- Suggest prerequisites, projects, certifications, and career guidance at every stage
- Continuously adapt recommendations based on learner progress
- Answer queries about courses, skills, career options, certifications, and industry trends
- Track learning progress and celebrate achievements
- Provide motivational guidance and study tips

## COMMUNICATION STYLE
- Tone: {tone}
- Language: {language}
- Always explain WHY you recommend something
- Use bullet points and numbered lists for clarity
- End every response with an encouraging next step or motivational tip
- Use emojis sparingly but effectively 🎯

## CURRENT LEARNER PROFILE
- Name: {learner_name}
- Career Goal: {career_goal}
- Current Skill Level: {skill_level}
- Learning Style: {learning_style}
- Interests: {interests}
- Completed Courses: {completed_courses}
- Current Learning Streak: {streak_days} days

## INSTRUCTIONS
1. Always personalise responses to the learner's profile above.
2. When recommending courses, include: title, provider, level, why it fits the learner.
3. When generating a roadmap, output valid JSON in the format described in your training.
4. When providing career guidance, include job titles, required skills, and next steps.
5. Keep responses focused on learning and career development.
6. If the learner seems discouraged, provide extra encouragement and simplify recommendations.
7. Never make up specific course URLs — describe the resource type and where to find it.
8. Refuse politely to answer anything unrelated to learning and career development.
""",
}
# ═════════════════════════════════════════════════════════════════════════════


class LearnMateAgent:
    """IBM watsonx.ai–powered learning assistant agent."""

    def __init__(self):
        self.api_key    = (os.getenv("WATSONX_API_KEY") or "").strip()
        self.project_id = (os.getenv("WATSONX_PROJECT_ID") or "").strip()
        self.url        = (os.getenv("WATSONX_URL") or "https://us-south.ml.cloud.ibm.com").strip()
        self.model_id   = (os.getenv("WATSONX_MODEL_ID") or "meta-llama/llama-3-3-70b-instruct").strip()
        self._model     = None
        self._initialised = False

    # ── Initialisation ────────────────────────────────────────────────────────
    def _init_model(self) -> bool:
        """Lazily initialise the watsonx.ai model client."""
        if self._initialised:
            return True
        # Bail out gracefully if package or credentials are missing
        if not _WATSONX_AVAILABLE:
            print("[LearnMateAgent] ibm-watsonx-ai not installed — using demo mode.")
            return False
        if not self.api_key or self.api_key in ("your-ibm-watsonx-api-key", ""):
            print("[LearnMateAgent] WATSONX_API_KEY not set — using demo mode.")
            return False
        if not self.project_id or self.project_id in ("your-watsonx-project-id", ""):
            print("[LearnMateAgent] WATSONX_PROJECT_ID not set — using demo mode.")
            return False
        try:
            credentials = Credentials(url=self.url, api_key=self.api_key)
            params = {
                GenParams.MAX_NEW_TOKENS: 1500,
                GenParams.TEMPERATURE: 0.7,
                GenParams.TOP_P: 0.9,
                GenParams.TOP_K: 50,
                GenParams.REPETITION_PENALTY: 1.1,
            }
            self._model = ModelInference(
                model_id=self.model_id,
                params=params,
                credentials=credentials,
                project_id=self.project_id,
            )
            self._initialised = True
            print(f"[LearnMateAgent] Connected to watsonx.ai — model: {self.model_id}")
            return True
        except Exception as exc:  # noqa: BLE001
            print(f"[LearnMateAgent] watsonx.ai init error: {exc}")
            return False

    # ── System prompt builder ─────────────────────────────────────────────────
    def _build_system_prompt(self, user_profile: dict) -> str:
        tmpl = AGENT_INSTRUCTIONS["system_prompt_template"]
        identity = AGENT_INSTRUCTIONS["identity"]
        style = AGENT_INSTRUCTIONS["communication_style"]
        completed = ", ".join(user_profile.get("completed_courses", [])) or "None yet"
        return tmpl.format(
            agent_name=identity["name"],
            agent_role=identity["role"],
            agent_tagline=identity["tagline"],
            tone=style["tone"],
            language=style["language"],
            learner_name=user_profile.get("full_name") or user_profile.get("username", "Learner"),
            career_goal=user_profile.get("career_goal") or "Not specified",
            skill_level=user_profile.get("skill_level", "beginner"),
            learning_style=user_profile.get("learning_style") or "Not specified",
            interests=user_profile.get("interests") or "Not specified",
            completed_courses=completed,
            streak_days=user_profile.get("streak_days", 0),
        )

    # ── Conversation history formatter ────────────────────────────────────────
    def _format_conversation(self, system_prompt: str, history: list[dict], user_message: str) -> str:
        """Build a prompt using Llama 3 chat template format."""
        # Llama 3 uses <|begin_of_text|> + <|start_header_id|>role<|end_header_id|> format
        parts = [
            "<|begin_of_text|>",
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>",
        ]
        # Include last 8 turns to stay within context limits
        for turn in history[-8:]:
            role = "user" if turn["role"] == "user" else "assistant"
            parts.append(f"<|start_header_id|>{role}<|end_header_id|>\n\n{turn['content']}<|eot_id|>")
        parts.append(f"<|start_header_id|>user<|end_header_id|>\n\n{user_message}<|eot_id|>")
        parts.append("<|start_header_id|>assistant<|end_header_id|>\n\n")
        return "".join(parts)

    # ── Core chat ─────────────────────────────────────────────────────────────
    def chat(self, user_message: str, history: list[dict], user_profile: dict) -> str:
        """
        Generate an AI response given the conversation history and learner profile.
        Falls back to an offline demo response when watsonx.ai is not configured.
        """
        if not self._init_model():
            return self._demo_response(user_message, user_profile)

        system_prompt = self._build_system_prompt(user_profile)
        prompt = self._format_conversation(system_prompt, history, user_message)

        try:
            response = self._model.generate_text(prompt=prompt)
            return response.strip() if response else "I couldn't generate a response. Please try again."
        except Exception as exc:  # noqa: BLE001
            print(f"[LearnMateAgent] generation error: {exc}")
            return self._demo_response(user_message, user_profile)

    # ── Roadmap generation ────────────────────────────────────────────────────
    def generate_roadmap(self, career_goal: str, skill_level: str, interests: str, user_profile: dict) -> dict:
        """
        Generate a structured JSON learning roadmap.
        Returns a dict with keys: title, career_goal, stages (list).
        """
        rg = AGENT_INSTRUCTIONS["roadmap_generation"]
        stages_info = ", ".join(rg["stages"])

        prompt_text = f"""Generate a detailed learning roadmap as valid JSON for the following learner:
- Career Goal: {career_goal}
- Current Skill Level: {skill_level}
- Interests / Background: {interests}

The JSON MUST follow this exact structure:
{{
  "title": "Learning Roadmap for {career_goal}",
  "career_goal": "{career_goal}",
  "total_estimated_weeks": <integer>,
  "stages": [
    {{
      "stage_name": "<one of: {stages_info}>",
      "description": "<what this stage covers>",
      "estimated_weeks": <integer>,
      "topics": ["topic1", "topic2", ...],
      "resources": [
        {{"title": "<resource name>", "type": "<course|book|tutorial|video>", "provider": "<name>", "free": <true|false>}}
      ],
      "projects": ["project1", "project2"],
      "certifications": ["cert1"],
      "milestone": "<what the learner can do after completing this stage>"
    }}
  ],
  "career_outcomes": ["job title 1", "job title 2"],
  "next_steps": "<motivational closing paragraph>"
}}

Return ONLY the JSON object, no extra text."""

        if not self._init_model():
            return self._demo_roadmap(career_goal, skill_level)

        system_prompt = self._build_system_prompt(user_profile)
        full_prompt = (
            "<|begin_of_text|>"
            f"<|start_header_id|>system<|end_header_id|>\n\n{system_prompt}<|eot_id|>"
            f"<|start_header_id|>user<|end_header_id|>\n\n{prompt_text}<|eot_id|>"
            "<|start_header_id|>assistant<|end_header_id|>\n\n"
        )

        try:
            raw = self._model.generate_text(prompt=full_prompt)
            # Extract the first JSON object from the response
            match = re.search(r"\{.*\}", raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as exc:  # noqa: BLE001
            print(f"[LearnMateAgent] roadmap error: {exc}")

        return self._demo_roadmap(career_goal, skill_level)

    # ── Course recommendations ────────────────────────────────────────────────
    def recommend_courses(self, user_profile: dict, topic: str | None = None) -> str:
        """Generate personalised course recommendations."""
        rs = AGENT_INSTRUCTIONS["recommendation_strategy"]
        max_recs = rs["max_recommendations_per_response"]

        goal = user_profile.get("career_goal") or "technology"
        level = user_profile.get("skill_level", "beginner")
        t = topic or goal

        prompt_text = (
            f"Recommend {max_recs} specific courses or learning resources for a {level}-level "
            f"learner who wants to become a {goal} and is interested in {t}. "
            f"For each resource: provide the title, provider, level, why it fits this learner, "
            f"and a brief description. Format as a numbered list."
        )

        history = [{"role": "user", "content": prompt_text}]
        return self.chat(prompt_text, [], user_profile)

    # ── Skill assessment feedback ─────────────────────────────────────────────
    def assess_skill(self, domain: str, answers: list[dict], user_profile: dict) -> dict:
        """Evaluate a skill-assessment quiz and return level + feedback."""
        correct = sum(1 for a in answers if a.get("correct", False))
        total = len(answers) if answers else 1
        score = round((correct / total) * 100, 1)

        if score >= 80:
            level = "advanced"
        elif score >= 50:
            level = "intermediate"
        else:
            level = "beginner"

        prompt_text = (
            f"A learner completed a {domain} skill assessment and scored {score}% ({correct}/{total} correct). "
            f"Based on this, their level is {level}. Provide:\n"
            f"1. A brief, encouraging assessment of their current skill level\n"
            f"2. Key areas to focus on next\n"
            f"3. Three specific resources to strengthen their knowledge\n"
            f"4. An estimated timeline to reach the next skill level\n"
            f"Keep it concise and motivating."
        )

        feedback_text = self.chat(prompt_text, [], user_profile)
        return {"score": score, "level": level, "feedback": feedback_text}

    # ── Demo / fallback responses ─────────────────────────────────────────────
    def _demo_response(self, message: str, user_profile: dict) -> str:
        """Offline demo response when watsonx.ai is not configured."""
        name = user_profile.get("full_name") or user_profile.get("username", "Learner")
        goal = user_profile.get("career_goal") or "your career goal"
        level = user_profile.get("skill_level", "beginner")
        msg_lower = message.lower()

        identity = AGENT_INSTRUCTIONS["identity"]

        if any(w in msg_lower for w in ["hello", "hi", "hey", "start"]):
            return (
                f"👋 Hello {name}! I'm **{identity['name']}**, your personalised learning assistant.\n\n"
                f"I can see you're aiming to become a **{goal}** at the **{level}** level — great choice! "
                f"Here's what I can help you with:\n\n"
                f"- 🗺️ **Personalised roadmaps** from beginner to expert\n"
                f"- 📚 **Course & resource recommendations** tailored to you\n"
                f"- 🏆 **Skill assessments** to gauge your current level\n"
                f"- 💼 **Career guidance** including job titles and portfolio tips\n"
                f"- 🔥 **Progress tracking** with streaks and XP rewards\n\n"
                f"What would you like to explore first? You can ask me things like:\n"
                f'*"Create my learning roadmap"*, *"Recommend courses for Python"*, or *"How do I become a data scientist?"*\n\n'
                f"🎯 **Tip:** The more you tell me about your goals and interests, the better I can personalise your journey!"
            )

        if any(w in msg_lower for w in ["roadmap", "plan", "path"]):
            return (
                f"🗺️ Great, {name}! Let me outline a personalised roadmap for **{goal}**.\n\n"
                f"Based on your **{level}** skill level, here's a high-level path:\n\n"
                f"**Stage 1 — Foundation (4–6 weeks)**\n"
                f"- Core programming fundamentals\n- Problem-solving & algorithms\n- Version control (Git)\n\n"
                f"**Stage 2 — Core Skills (8–10 weeks)**\n"
                f"- Domain-specific tools & frameworks\n- Build 2–3 guided projects\n\n"
                f"**Stage 3 — Intermediate (10–12 weeks)**\n"
                f"- Advanced concepts & design patterns\n- Real-world projects & open source contributions\n\n"
                f"**Stage 4 — Advanced (12+ weeks)**\n"
                f"- Specialisation, certifications, portfolio polish\n- Job application preparation\n\n"
                f"👉 **Next step:** Click the **'Generate Roadmap'** button in the Roadmap tab for a fully detailed, interactive version tailored to you!"
            )

        if any(w in msg_lower for w in ["course", "learn", "resource", "study"]):
            return (
                f"📚 Here are some highly recommended resources for **{goal}** at the **{level}** level:\n\n"
                f"1. **Coursera Specialisations** — Structured multi-course tracks with certificates\n"
                f"   *Why?* Rigorous curriculum and recognised by employers\n\n"
                f"2. **freeCodeCamp** — Free, project-based learning with certifications\n"
                f"   *Why?* Hands-on practice with real projects\n\n"
                f"3. **Kaggle Learn** (if data-focused) — Short, practical micro-courses\n"
                f"   *Why?* Learn by doing with real datasets\n\n"
                f"4. **The Odin Project** (if web-focused) — Full-stack curriculum, completely free\n"
                f"   *Why?* Industry-aligned, community-driven\n\n"
                f"5. **MIT OpenCourseWare** — University-level content for free\n"
                f"   *Why?* Deep theoretical foundation\n\n"
                f"💡 **Pro tip:** Combine video courses with hands-on projects — aim for a 60/40 learning-to-doing ratio!"
            )

        if any(w in msg_lower for w in ["career", "job", "salary", "role"]):
            return (
                f"💼 Excellent question about career paths for **{goal}**!\n\n"
                f"**Typical job titles you can target:**\n"
                f"- Junior → Mid-level → Senior → Lead/Principal\n\n"
                f"**Key skills employers look for:**\n"
                f"- Strong portfolio with 3–5 real projects\n"
                f"- At least one industry-recognised certification\n"
                f"- Problem-solving demonstrated through coding challenges\n"
                f"- Soft skills: communication, teamwork, continuous learning\n\n"
                f"**Salary range (US, approximate):**\n"
                f"- Junior: $60k–$90k | Mid: $90k–$130k | Senior: $130k–$180k+\n\n"
                f"**Your next career steps:**\n"
                f"1. Complete your learning roadmap milestones ✅\n"
                f"2. Build a portfolio on GitHub 💻\n"
                f"3. Network on LinkedIn and attend meetups 🤝\n"
                f"4. Apply for internships or junior roles while still learning 🚀\n\n"
                f"🌟 **Remember:** Every expert was once a beginner. Stay consistent!"
            )

        # Generic response
        return (
            f"🤔 That's a great question, {name}! I'm here to help you on your journey to become a **{goal}**.\n\n"
            f"Here's what I can help you with right now:\n\n"
            f"- 📚 **Course recommendations** — Ask: *'Recommend courses for Python'*\n"
            f"- 🗺️ **Learning roadmap** — Ask: *'Create my learning roadmap'*\n"
            f"- 💼 **Career guidance** — Ask: *'What jobs can I get as a data scientist?'*\n"
            f"- 🏆 **Skill tips** — Ask: *'How do I improve my machine learning skills?'*\n\n"
            f"⚙️ **Note:** Full AI responses are available when IBM watsonx.ai credentials are configured in `.env`.\n\n"
            f"🎯 Keep going — you're making great progress!"
        )

    def _demo_roadmap(self, career_goal: str, skill_level: str) -> dict:
        """Offline demo roadmap when watsonx.ai is not configured."""
        return {
            "title": f"Learning Roadmap: {career_goal}",
            "career_goal": career_goal,
            "total_estimated_weeks": 40,
            "stages": [
                {
                    "stage_name": "Foundation",
                    "description": "Build the essential fundamentals needed for your journey.",
                    "estimated_weeks": 6,
                    "topics": ["Programming Basics", "Problem Solving", "Git & Version Control", "Command Line"],
                    "resources": [
                        {"title": "CS50: Introduction to Computer Science", "type": "course", "provider": "Harvard / edX", "free": True},
                        {"title": "The Missing Semester of CS Education", "type": "course", "provider": "MIT", "free": True},
                        {"title": "Git & GitHub Crash Course", "type": "video", "provider": "freeCodeCamp", "free": True},
                    ],
                    "projects": ["Build a command-line calculator", "Create a personal portfolio website"],
                    "certifications": [],
                    "milestone": "You can write clean code, use Git, and solve basic algorithmic problems.",
                },
                {
                    "stage_name": "Core Skills",
                    "description": f"Develop the core domain skills required for {career_goal}.",
                    "estimated_weeks": 10,
                    "topics": ["Domain Frameworks", "Data Structures & Algorithms", "APIs & Integration", "Testing"],
                    "resources": [
                        {"title": "Domain Specialisation Course", "type": "course", "provider": "Coursera", "free": False},
                        {"title": "LeetCode / HackerRank", "type": "tutorial", "provider": "LeetCode", "free": True},
                        {"title": "REST API Design & Development", "type": "course", "provider": "Udemy", "free": False},
                    ],
                    "projects": ["Build a full CRUD application", "Integrate a third-party API into a project"],
                    "certifications": ["IBM Professional Certificate (Coursera)"],
                    "milestone": f"You can build and deploy functional {career_goal} projects independently.",
                },
                {
                    "stage_name": "Intermediate",
                    "description": "Deepen your expertise with advanced concepts and real-world projects.",
                    "estimated_weeks": 12,
                    "topics": ["Design Patterns", "System Design", "Cloud Basics", "Collaboration & Agile"],
                    "resources": [
                        {"title": "System Design Primer", "type": "book", "provider": "GitHub", "free": True},
                        {"title": "AWS Cloud Practitioner Prep", "type": "course", "provider": "AWS Training", "free": True},
                        {"title": "Clean Code", "type": "book", "provider": "O'Reilly", "free": False},
                    ],
                    "projects": ["Contribute to an open-source project", "Build and deploy a cloud-hosted app"],
                    "certifications": ["AWS Certified Cloud Practitioner"],
                    "milestone": "You can architect and deploy scalable systems and collaborate on production codebases.",
                },
                {
                    "stage_name": "Advanced",
                    "description": "Specialise, certify, and prepare for senior-level roles.",
                    "estimated_weeks": 12,
                    "topics": ["Advanced Specialisation", "Performance Optimisation", "Security Best Practices", "Leadership"],
                    "resources": [
                        {"title": "Advanced Specialisation Course", "type": "course", "provider": "Coursera / edX", "free": False},
                        {"title": "Security & Best Practices Guide", "type": "tutorial", "provider": "OWASP", "free": True},
                    ],
                    "projects": ["Build a capstone project showcasing full expertise", "Write a technical blog series"],
                    "certifications": ["Professional Certification in your domain"],
                    "milestone": f"You are job-ready for mid-to-senior {career_goal} positions with a strong portfolio.",
                },
            ],
            "career_outcomes": [
                f"Junior {career_goal}",
                f"Mid-level {career_goal}",
                f"Senior {career_goal}",
                f"Lead / Principal {career_goal}",
            ],
            "next_steps": (
                f"You're on your way to becoming a {career_goal}! Start with Stage 1, "
                "set aside at least 1 hour per day for focused learning, and track your progress "
                "in the LearnMate dashboard. Remember: consistency beats intensity. "
                "You've got this! 🚀"
            ),
        }


# Singleton agent instance
agent = LearnMateAgent()

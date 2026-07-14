# 🎓 LearnMate — AI-Powered Personalised Learning Assistant

> Built with Python Flask · IBM watsonx.ai · Bootstrap 5 · SQLite/PostgreSQL

LearnMate is a full-stack AI learning platform that creates personalised learning roadmaps, recommends courses, assesses skills, and guides learners toward their career goals using IBM watsonx.ai.

---

## ✨ Features

| Feature | Description |
|---|---|
| 🤖 **AI Chat** | 24/7 chatbot powered by IBM watsonx.ai (Granite) |
| 🗺️ **Learning Roadmaps** | AI-generated roadmaps from beginner → expert |
| 📚 **Course Library** | 18+ curated courses across 10+ tech domains |
| 🏆 **Skill Assessment** | Interactive quizzes with AI feedback |
| 📊 **Progress Dashboard** | XP, streaks, badges, and activity tracking |
| 👤 **User Profiles** | Career goals, learning style, interests |
| 🌙 **Dark Mode** | Full light/dark theme with persistence |
| 📱 **Responsive UI** | Mobile-first Bootstrap 5 design |

---

## 🏗️ Project Structure

```
learnmate/
├── app.py                     # Flask application factory + entry point
├── models.py                  # SQLAlchemy ORM models
├── agent.py                   # IBM watsonx.ai AI agent + AGENT_INSTRUCTIONS
├── sample_data.py             # 18 seed courses
├── requirements.txt
├── .env.example               # Environment variable template
│
├── routes/
│   ├── __init__.py
│   ├── auth.py                # Login, register, logout
│   ├── dashboard.py           # Main dashboard
│   ├── chat.py                # AI chatbot routes
│   ├── courses.py             # Course browse, enroll, progress
│   ├── roadmap.py             # Roadmap generation & display
│   ├── assessment.py          # Skill assessment quiz
│   ├── profile.py             # Profile view & update
│   └── api.py                 # JSON API endpoints
│
├── templates/
│   ├── base.html              # Navbar, flash messages, footer
│   ├── index.html             # Landing page
│   ├── login.html
│   ├── register.html
│   ├── setup.html             # Multi-step profile setup wizard
│   ├── dashboard.html
│   ├── chat.html
│   ├── courses.html
│   ├── roadmap.html
│   ├── assessment.html
│   ├── profile.html
│   └── partials/
│       └── roadmap_content.html
│
└── static/
    ├── css/style.css          # Full custom stylesheet
    └── js/main.js             # Chat, roadmap, assessment, dark mode
```

---

## 🚀 Quick Start

### 1. Clone & enter directory

```bash
cd learnmate
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
```

Edit `.env` and fill in:

```env
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_hex(32))">
WATSONX_API_KEY=<your IBM Cloud API key>
WATSONX_PROJECT_ID=<your watsonx.ai project ID>
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

> 💡 The app works **without** watsonx credentials — it falls back to intelligent demo responses so you can explore all features immediately.

### 5. Run the application

```bash
python app.py
```

Visit **http://localhost:5000** 🎉

---

## 🤖 IBM watsonx.ai Setup

1. Log in to [IBM Cloud](https://cloud.ibm.com)
2. Create a **watsonx.ai** instance
3. Create a **Project** and note the Project ID
4. Generate an **API key** from IAM → API keys
5. Copy values to your `.env` file

Supported models (set `WATSONX_MODEL_ID`):
- `ibm/granite-13b-chat-v2` *(default, recommended)*
- `ibm/granite-20b-code-instruct-v1`
- `meta-llama/llama-3-70b-instruct`

---

## 🎛️ Customising Agent Behaviour

All AI agent behaviour is controlled via the `AGENT_INSTRUCTIONS` dictionary in [`agent.py`](agent.py).

```python
AGENT_INSTRUCTIONS = {
    "identity": {
        "name": "LearnMate AI",           # Change agent name
        "role": "Personalised Learning Assistant",
    },
    "communication_style": {
        "tone": "friendly, encouraging, and professional",
        "use_emojis": True,               # Toggle emoji use
    },
    "recommendation_strategy": {
        "max_recommendations_per_response": 5,  # More/fewer recs
        "prioritize_free_resources": False,      # Prefer free courses
        "include_certifications": True,
    },
    "roadmap_generation": {
        "stages": ["Foundation", "Core Skills", "Intermediate", "Advanced", "Expert"],
        "always_include_projects": True,
    },
    "career_guidance": {
        "include_salary_ranges": True,
        "include_interview_tips": True,
    },
    ...
}
```

---

## 📦 Database

The app uses **SQLite** by default (file: `instance/learnmate.db`).

For production, set `DATABASE_URL` to a PostgreSQL connection string:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/learnmate
```

Install the PostgreSQL driver:
```bash
pip install psycopg2-binary
```

---

## 🌐 Deployment

### Option A — Gunicorn (Linux/macOS)

```bash
gunicorn -w 4 -b 0.0.0.0:5000 "app:app"
```

### Option B — Docker

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "app:app"]
```

```bash
docker build -t learnmate .
docker run -p 5000:5000 --env-file .env learnmate
```

### Option C — IBM Cloud Code Engine

```bash
ibmcloud ce application create \
  --name learnmate \
  --image icr.io/yourrepo/learnmate:latest \
  --port 5000 \
  --env-from-secret learnmate-secrets
```

### Option D — Heroku

```bash
heroku create learnmate-app
heroku config:set SECRET_KEY=... WATSONX_API_KEY=... WATSONX_PROJECT_ID=...
git push heroku main
```

---

## 🧪 Running Without watsonx.ai

The application includes a complete **offline demo mode**. When `WATSONX_API_KEY` or `WATSONX_PROJECT_ID` are missing:

- The chatbot responds with intelligent, context-aware demo messages
- Roadmap generation returns a structured 4-stage demo roadmap
- All other features (courses, assessments, progress) work fully

---

## 📋 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Landing page |
| GET/POST | `/login` | User login |
| GET/POST | `/register` | User registration |
| GET | `/dashboard` | Main dashboard |
| GET | `/chat` | AI chat interface |
| POST | `/chat/send` | Send chat message (JSON) |
| GET | `/courses` | Browse & search courses |
| POST | `/courses/<id>/enroll` | Enroll in a course |
| POST | `/courses/<id>/progress` | Update progress |
| GET | `/roadmap` | View roadmap |
| POST | `/roadmap/generate` | Generate AI roadmap |
| GET | `/assessment` | Skill assessment |
| GET | `/assessment/quiz/<domain>` | Get quiz questions |
| POST | `/assessment/submit` | Submit quiz |
| GET | `/profile` | User profile |
| POST | `/profile/update` | Update profile |
| GET | `/api/stats` | User stats JSON |

---

## 🛡️ Security Notes

- CSRF protection on all forms via Flask-WTF
- Passwords hashed with Werkzeug's PBKDF2
- Login required on all protected routes
- Environment secrets via `.env` (never commit to git)

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">
  <strong>Made with ❤️ using IBM watsonx.ai · LearnMate</strong>
</div>

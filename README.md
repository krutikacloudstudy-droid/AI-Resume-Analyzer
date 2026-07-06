# 🧠 AI Resume Analyzer & Career Assistant

An AI-powered web application that analyzes a candidate's resume (PDF) and
generates a complete career report: resume/ATS scores, skill gap analysis,
job-role suggestions, salary estimation, a personalized career roadmap,
resume improvement tips, and mock interview questions — all powered by the
**Google Gemini API**.

Built as a college mini project using **Python Flask**, **SQLite**, and a
modern **glassmorphism** UI inspired by ChatGPT-style dashboards.

---

## ✨ Features

- 🎨 Modern glassmorphism landing page with animated hero section
- 📤 Drag-and-drop PDF resume upload with client-side validation
- ⏳ Animated loading state with progress bar during analysis
- 📄 Resume text extraction using `pdfplumber`
- 🤖 AI analysis powered by the latest `google-genai` SDK (Gemini)
- 📊 Resume Score & ATS Score (visual progress rings)
- 🧩 Technical skills, soft skills, and missing skills detection
- 💼 Work experience, education, certifications, and projects extraction
- 🎯 Suggested job roles with match percentage
- 💰 Salary estimation (entry / mid / senior level)
- 🗺️ Personalized short/mid/long-term career roadmap
- 🛠️ Actionable resume improvement suggestions
- 🗣️ AI-generated interview questions (technical, behavioral, situational)
- 📥 Downloadable plain-text analysis report
- 🕓 Recent analysis history sidebar (SQLite backed)
- ⚠️ Custom error pages (404 / 500 / file-too-large)
- 📱 Fully responsive across desktop, tablet, and mobile

---

## 🧱 Tech Stack

| Layer      | Technology                              |
|------------|------------------------------------------|
| Frontend   | HTML5, CSS3, Bootstrap 5, JavaScript, Font Awesome, Bootstrap Icons |
| Backend    | Python 3.10+, Flask 3.x                  |
| Database   | SQLite                                   |
| AI Engine  | Google Gemini (`google-genai` SDK)       |
| PDF Parsing| pdfplumber                               |
| Config     | python-dotenv                            |

---

## 📁 Folder Structure

```
AI-Resume-Analyzer/
│
├── app.py                  # Flask application (routes, error handlers)
├── utils.py                # PDF parsing, Gemini AI calls, DB helpers
├── config.py                # App configuration & environment loading
├── requirements.txt         # Python dependencies
├── README.md                 # Project documentation
├── .env.example              # Sample environment variables
├── database.db               # SQLite database (auto-created on first run)
│
├── uploads/                  # Temporary storage for uploaded PDFs
│
├── templates/
│   ├── layout.html            # Base template (navbar, footer, flash msgs)
│   ├── index.html             # Landing page
│   ├── dashboard.html         # Upload dashboard + history sidebar
│   ├── result.html            # Full analysis report page
│   └── error.html             # Generic error page (404 / 500)
│
└── static/
    ├── css/
    │   ├── style.css           # Global design system & landing page styles
    │   └── dashboard.css       # Dashboard & result page styles
    ├── js/
    │   └── main.js              # Drag-drop upload, validation, progress bar
    └── images/                  # Static image assets
```

---

## ⚙️ Installation & Setup

### 1. Clone or extract the project

```bash
cd AI-Resume-Analyzer
```

### 2. Create and activate a virtual environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example file and add your Gemini API key:

```bash
cp .env.example .env
```

Edit `.env`:

```
SECRET_KEY=your-random-secret-key
FLASK_DEBUG=True
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

> Get a free Gemini API key from **[Google AI Studio](https://aistudio.google.com/app/apikey)**.

### 5. Run the application

```bash
python app.py
```

The app will be available at **http://127.0.0.1:5000**

---

## 🔑 Getting a Gemini API Key

1. Visit https://aistudio.google.com/app/apikey
2. Sign in with your Google account
3. Click **Create API Key**
4. Copy the key into your `.env` file as `GEMINI_API_KEY`

---

## 🖥️ Usage

1. Open the landing page and click **Analyze My Resume**
2. Drag & drop (or browse) a PDF resume — maximum 8MB
3. Click **Analyze Resume** and wait for the AI to process it
4. View your full report: scores, skills, roles, salary, roadmap & more
5. Download the report as a text file, or analyze another resume

---

## 📸 Screenshots

> Add your own screenshots here after running the project locally.

| Page | Preview |
|------|---------|
| Landing Page | `screenshots/landing.png` |
| Dashboard (Upload) | `screenshots/dashboard.png` |
| Result Page | `screenshots/result.png` |

---

## 🧪 Notes on the AI Analysis

- Uploaded PDFs are parsed in-memory using `pdfplumber` and **deleted immediately**
  after analysis — only the structured AI result is stored in SQLite.
- The Gemini model is prompted to return strict JSON following a fixed schema,
  which is then rendered into the dashboard UI.
- Scanned/image-only PDF resumes cannot be parsed since they contain no
  extractable text; use a text-based PDF export for best results.

---

## 🚀 Future Improvements

- 🔐 User authentication & personal analysis history
- 📄 Export analysis report as a formatted PDF (instead of plain text)
- 🌐 Multi-language resume support
- 📈 Resume version comparison (track improvement over time)
- 🧠 Fine-tuned scoring per industry (Tech, Finance, Healthcare, etc.)
- 🗂️ Bulk resume analysis for recruiters
- ☁️ Cloud deployment guide (Render / Railway / Azure)
- 🌗 Full light/dark theme toggle switch in the UI

---

## 📜 License

This project was built for academic/educational purposes as a college mini
project. Feel free to fork and extend it for your own learning.

# AI Project Analyzer 🤖

An agentic AI-powered evaluation tool designed to analyze student programming projects. It combines static language/framework detection with LLM-based semantic understanding to map project skills, generate custom interview questions, and identify architectural strengths and gaps.

---

## 🏗️ Project Architecture

```
AI ANALYSER/
├── frontend/             # Client-side web dashboard
│   ├── css/              # Stylesheets
│   ├── js/               # UI and Chart rendering logic
│   └── index.html        # Upload & Dashboard UI
│
├── backend/              # Flask-based REST API
│   ├── app/
│   │   ├── api/          # Blueprints and request schemas
│   │   ├── services/     # Parsing, Embedding, and LLM orchestration
│   │   └── models/       # Skill catalog taxomony JSON
│   └── .env              # Environment configurations
```

---

## 🛠️ Tech Stack & Dependencies

### Frontend
- **Structure & Styling:** Vanilla HTML5 & Tailwind CSS
- **Interactions:** Vanilla ES6 JavaScript (Drag & Drop, transition handlers)
- **Visuals:** [Chart.js](https://www.chartjs.org/) (for skill distribution and confidence charts)

### Backend
- **Framework:** Python Flask with CORS support
- **Vector Search:** FAISS (for codebase retrieval indexing)
- **API integrations:** Gemini API (evaluation and code-review) & Cohere Embeddings

---

## 🚀 Key Features

- **ZIP File Processing:** Safe extraction, Zip Slip protection, and automatic formatting of filename as project title.
- **Static Multi-Language Detection:** Computes Lines of Code (LOC) and percentage breakdown for Python, JS, TS, Java, Go, Dart, C++, and more.
- **Framework & ML Library Classifier:** Statically detects frontend/backend frameworks (Flask, FastAPI, Django, React, Flutter, NestJS, Spring Boot) and ML/Data Science modules (scikit-learn, TensorFlow, PyTorch, Pandas, NumPy).
- **Taxonomy Skill Mapping:** Identifies skills mapping back to a structured skill registry (using unique `skill_id`s, category, and descriptions).
- **Tailored Interview Generator:** Automatically builds conceptually relevant interview questions with expected answers and difficulty levels.
- **Architectural Auditing:** Generates cohesive narrative summaries pointing out code strengths and improvement gaps.

---

## ⚙️ Quick Start

### 1. Run the Backend API
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```
3. Ensure `.env` is populated with valid `GOOGLE_API_KEY` and `COHERE_API_KEY`.
4. Run the Flask server:
   ```bash
   python app/main.py
   ```
   *The API will run on `http://127.0.0.1:5000`.*

### 2. Run the Frontend
1. Open the [index.html](file:///home/bart-simpson/Code/INTERN/frontend/index.html) file directly in any modern browser:
   ```bash
   # On Linux/Ubuntu
   xdg-open frontend/index.html
   ```
2. Drag and drop your project ZIP or click to browse. Set the number of questions you want per skill, and hit **Analyze Project**.

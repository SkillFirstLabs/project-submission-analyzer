# 🎓 Project Evaluator AI

An AI-powered project evaluation platform that reviews student projects, asks intelligent follow-up questions, and generates a detailed performance report based on both the submitted code and the student's understanding.

Instead of relying only on source code, the system evaluates **how well a student understands what they have built**, making it useful for project reviews, academic evaluations, internships, and technical assessments.

---

# ✨ Key Features

* 📦 Upload any project as a ZIP file
* 🔍 Automatically analyze project structure and source code
* 🧠 Detect technologies and frameworks used in the project
* ❓ Generate **exactly two AI-powered questions**

  * One conceptual question
  * One code-specific question
* 💬 Evaluate answers along with the project implementation
* 📊 Generate a comprehensive evaluation report with scores and feedback
* ⚡ Real-time progress updates during analysis
* 🎨 Clean and responsive React interface

---

# 🚀 How It Works

```text
                Project Submission
                        │
                        ▼
            Upload ZIP + Project Details
                        │
                        ▼
          Secure ZIP Extraction & Analysis
                        │
                        ▼
         Detect Languages & Technologies
                        │
                        ▼
        AI Generates Exactly 2 Questions
                        │
                        ▼
           Student Answers Questions
                        │
                        ▼
      AI Evaluates Code + Student Answers
                        │
                        ▼
          Comprehensive Evaluation Report
```

---

# 🛠 Tech Stack

## Backend

* Flask
* Google Gemini API
* Flask-CORS
* Python Dotenv

## Frontend

* React 18
* Tailwind CSS
* Axios
* Lucide React

---

# 📂 Project Structure

```
project-evaluator-ai/
│
├── backend/
│   ├── app.py
│   ├── evaluator.py
│   ├── requirements.txt
│   ├── uploads/
│   └── extracted_projects/
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
└── README.md
```

---

# ⚙️ Installation

## Prerequisites

* Python 3.8+
* Node.js 16+
* Google Gemini API Key

---

## Backend Setup

Clone the repository and move into the backend folder.

```bash
cd backend
```

Create a virtual environment.

```bash
python -m venv venv
```

Activate it.

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Create a `.env` file.

```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
FLASK_ENV=development
FLASK_PORT=5000
```

Start the Flask server.

```bash
python app.py
```

Backend runs on:

```
http://localhost:5000
```

---

## Frontend Setup

Move to the frontend folder.

```bash
cd frontend
```

Install dependencies.

```bash
npm install
```

Run the development server.

```bash
npm start
```

Frontend runs on:

```
http://localhost:3000
```

---

# 📡 API Endpoints

## Submit Project

```
POST /submit
```

Uploads a ZIP file along with project information.

### Request

```
multipart/form-data
```

Fields

* title
* description
* zip

### Response

```json
{
  "job_id": "uuid",
  "status": "uploaded"
}
```

---

## Check Processing Status

```
GET /status/{job_id}
```

Possible states

* uploaded
* extracting
* analyzing
* ready_for_questions
* evaluating
* done

---

## Fetch AI Questions

```
GET /questions/{job_id}
```

Returns exactly two questions.

```json
{
  "conceptual_question": {
    "question": "...",
    "skill": "React"
  },
  "code_question": {
    "question": "...",
    "skill": "Python"
  }
}
```

---

## Submit Answers

```
POST /answers/{job_id}
```

```json
{
  "conceptual_answer": "...",
  "code_answer": "..."
}
```

---

## Get Final Evaluation

```
GET /result/{job_id}
```

Returns:

* Final score
* Conceptual score
* Code understanding score
* Verdict
* Strengths
* Weaknesses
* Question analysis
* Final summary

---

# 🧠 AI Evaluation Process

The evaluation is performed in two stages.

## Stage 1 — Project Analysis

The AI analyzes the uploaded project to understand:

* Project architecture
* Source code quality
* Technologies used
* Folder structure
* Coding practices

After analysis, the system generates **exactly two questions**:

* One conceptual question
* One project-specific coding question

---

## Stage 2 — Student Assessment

Once the student answers the questions, the AI evaluates:

### Project Implementation

* Code organization
* Best practices
* Complexity
* Completeness

### Conceptual Understanding

How well the student understands the technologies and concepts used.

### Code Understanding

Whether the student genuinely understands their own implementation.

---

# 📊 Evaluation Report

The final report includes:

* ✅ Overall Score (0–100)
* ✅ Conceptual Score
* ✅ Code Understanding Score
* ✅ Project Verdict
* ✅ Strengths
* ✅ Areas for Improvement
* ✅ Question-wise Feedback
* ✅ AI Summary

---

# 🔍 Automatic Skill Detection

The system detects technologies directly from the uploaded source code.

Supported technologies include:

* Python
* Java
* JavaScript
* TypeScript
* React
* Node.js
* HTML
* CSS
* SQL
* MongoDB
* REST APIs
* Git
* Docker

No skills are inferred without evidence from the project.

---

# 🧪 Testing the Application

1. Start the backend server.
2. Start the frontend.
3. Open the application.
4. Upload a project ZIP.
5. Wait for analysis to complete.
6. Answer the two AI-generated questions.
7. View the evaluation report.

---

# 📁 Recommended ZIP Contents

A valid submission should include source files such as:

```
.py
.js
.jsx
.ts
.tsx
.java
```

Optional but recommended:

* README.md
* package.json
* requirements.txt
* pom.xml
* Dockerfile
* Configuration files

---

# ⚠ Important Notes

* Only **two** questions are generated for each project.
* The final evaluation is generated **only after both questions are answered**.
* Questions are based on the uploaded project's actual source code.
* Skill detection is evidence-based and does not infer unsupported technologies.
* ZIP extraction is performed securely with validation checks.

---

# 🐞 Troubleshooting

### Backend doesn't start

* Verify Python is installed.
* Ensure port **5000** is available.
* Install all required dependencies.

### Frontend cannot connect

* Confirm the backend server is running.
* Verify the API URL is correct.

### Gemini API errors

* Check that your API key is valid.
* Ensure the API has available quota.
* Verify the `.env` configuration.

### ZIP extraction fails

* Make sure the ZIP file is not corrupted.
* Ensure it contains source code files.

---

# 🚀 Future Improvements

Possible enhancements include:

* User authentication
* Database integration
* Evaluation history
* Admin dashboard
* PDF report export
* Team project support
* Voice-based viva questions
* Advanced plagiarism detection
* Multi-language code analysis

---

# 📄 License

This project is intended for educational and demonstration purposes.

---

# 👨‍💻 Author

Developed as an AI-assisted project evaluation platform to simplify academic project reviews while assessing both implementation quality and conceptual understanding.

# Project Submission AI Analyzer

## Overview

Project Submission AI Analyzer is an AI-powered project evaluation platform built using FastAPI. It automatically analyzes uploaded project source code, detects technical skills, generates viva questions, performs live proctoring, evaluates candidate responses, and generates a final assessment report.

---

## Features

- Project ZIP Analysis
- Automatic Skill Detection
- AI-based Viva Question Generation
- Live Camera Proctoring
- Face Detection
- Multiple Face Detection
- Fullscreen Monitoring
- Copy/Paste Detection
- Tab Switching Detection
- Viva Answer Evaluation
- Project Outcome Evaluation
- Final Assessment Generation
- REST API using FastAPI
- Automated Testing using Pytest

---

## Technology Stack

### Backend

- FastAPI
- Python
- Pydantic

### Frontend

- HTML
- CSS
- JavaScript

### AI / Computer Vision

- MediaPipe
- OpenCV

### Testing

- Pytest

---

## Project Structure

```
project-submission-ai-analyzer/
│
├── app/
│   ├── services/
│   ├── static/
│   ├── templates/
│   ├── models.py
│   ├── main.py
│
├── tests/
│
├── requirements.txt
├── package.json
└── README.md
```

---

## Workflow

1. Upload Project ZIP
2. Analyze Source Code
3. Detect Skills
4. Generate Viva Questions
5. Start Proctored Viva
6. Monitor Candidate Activity
7. Evaluate Viva Answers
8. Evaluate Project Outcomes
9. Generate Final Assessment

---

## Proctoring Features

- Face Detection
- Multiple Face Detection
- Face Not Detected Warning
- Fullscreen Exit Detection
- Tab Switch Detection
- Copy/Paste Detection
- Integrity Score Calculation

---

## API Endpoints

| Method | Endpoint |
|---------|----------|
| GET | /health |
| POST | /analyze-submission |
| POST | /viva-session/start |
| POST | /viva-session/event |
| POST | /viva-session/end |
| POST | /viva-session/evaluate |
| POST | /final-assessment |

---

## Installation

Clone the repository

```bash
git clone https://github.com/SkillFirstLabs/project-submission-analyzer.git
```

Create virtual environment

```bash
python -m venv venv
```

Activate virtual environment

Windows

```bash
venv\Scripts\activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

Run the server

```bash
uvicorn app.main:app --reload
```

Open

```
http://127.0.0.1:8000
```

---

## Testing

Run all tests

```bash
pytest
```

Current Status

```
9 Tests Passed
```

---

## Future Improvements

- Database Integration
- User Authentication
- AI-based Answer Evaluation using LLMs
- Cloud Deployment
- Dashboard Analytics

---

## Author

HARIKARAMUTHUKUMAR M

Internship Project
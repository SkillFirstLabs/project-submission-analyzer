
# ProjectIQ
## AI-Powered Project Submission Analyzer

ProjectIQ is a FastAPI microservice that extracts and inspects a student's project ZIP file, programmatically detects implemented technical skills from a local skill catalog, evaluates the stated project outcomes against actual code evidence, and generates conceptual and codebase-specific interview questions. The analysis and reporting are synthesized using the Groq LPU API.

---

### Folder Structure

```text
projectiq/
├── app/
│   ├── main.py
│   ├── api/
│   │   └── analyzer.py
│   ├── models/
│   │   └── schemas.py
│   ├── services/
│   │   ├── zip_extractor.py
│   │   ├── skill_detector.py
│   │   ├── question_generator.py
│   │   ├── outcome_evaluator.py
│   │   └── report_builder.py
│   ├── utils/
│   │   └── helpers.py
│   └── config.py
│
├── data/
│   └── skill_catalog.json
│
├── tests/
│   ├── test_zip_security.py
│   └── test_response_schema.py
│
├── .env.example
├── requirements.txt
├── README.md
└── NOTES.md
```

---

### Setup Instructions

#### 1. Prerequisites
- Python 3.11+
- Git

#### 2. Installation Steps
1. Navigate to the project root directory:
   ```bash
   cd projectiq
   ```
2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell)
   .\.venv\Scripts\Activate.ps1
   # On macOS/Linux
   source .venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

#### 3. Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your Groq API Key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_goes_here
GROQ_MODEL=llama-3.3-70b-versatile
```

---

### Running the Server

Start the development server with Uvicorn:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
The interactive Swagger API documentation will be available at:
[http://localhost:8000/docs](http://localhost:8000/docs)

---

### API Example

You can test the endpoint using `curl` from your terminal:

```bash
curl -X POST "http://localhost:8000/analyze-submission" \
  -F "project_title=E-Commerce API" \
  -F "project_description=A RESTful API built using FastAPI with PostgreSQL" \
  -F "project_outcomes=Build REST API
Deploy using Docker" \
  -F "zip_file=@/path/to/student_project.zip" \
  -F "questions_per_skill=2"
```

---

### Example Response

```json
{
  "project_title": "E-Commerce API",
  "suggested_skills": [
    {
      "skill_id": "fastapi",
      "skill_name": "FastAPI",
      "confidence": 0.98,
      "rationale": "Detected from dependency declaration(s) 'fastapi' and import(s) 'fastapi' in source files."
    },
    {
      "skill_id": "docker",
      "skill_name": "Docker",
      "confidence": 0.95,
      "rationale": "Detected from configuration file(s) 'Dockerfile'."
    }
  ],
  "evaluation_report": {
    "skills": [
      {
        "skill_id": "fastapi",
        "skill_name": "FastAPI",
        "questions": [
          {
            "question_text": "What is dependency injection in FastAPI?",
            "question_focus": "conceptual",
            "expected_key_points": [
              "Depends function",
              "Loose coupling",
              "Testing mockability"
            ]
          },
          {
            "question_text": "In app/main.py, why was APIRouter used instead of defining routes directly?",
            "question_focus": "codebase_specific",
            "expected_key_points": [
              "Modular routing structure",
              "Scalability",
              "Grouping logical routes"
            ]
          }
        ]
      }
    ],
    "summary": {
      "overall_alignment": "strong",
      "alignment_score": 0.9,
      "narrative": "The project demonstrates solid REST API design. By separating routes into modules using APIRouter, the student shows strong FastAPI best practice alignment. Standard Docker configurations are also successfully supplied."
    },
    "outcome_evaluation": [
      {
        "stated_outcome": "Build REST API",
        "status": "met",
        "evidence": "app/main.py contains initialization of FastAPI and router registration.",
        "gap": null
      },
      {
        "stated_outcome": "Deploy using Docker",
        "status": "met",
        "evidence": "Dockerfile present with clean multi-stage build instructions.",
        "gap": null
      }
    ],
    "strengths": [
      "Well-structured directory organization.",
      "Appropriate usage of FastAPI routers for module organization."
    ],
    "gaps": [
      "Missing automated test cases in the codebase."
    ]
  },
  "metadata": {
    "files_analyzed": 5,
    "extraction_time_ms": 12,
    "model_tokens_used": 1240
  },
  "processing_time_ms": 2341
}
```

---

### Testing Instructions

Verify code functionality and safety protections by running the automated suite:

```bash
pytest -v
```
This runs the unit tests verifying:
- Safe extraction (anti-Zip Slip, anti-Zip Bomb).
- API request/response schema validations.
- Simulated API orchestration through service mocks.


# Project Submission AI Analyzer

An AI-powered backend service that analyzes software project submissions, extracts codebase evidence, detects demonstrated skills, and generates structured viva evaluation reports for mentors.

---

## Technical Stack

- **Backend Language**: Python 3.11+
- **API Framework**: FastAPI
- **Data Validation & Settings**: Pydantic / Pydantic Settings
- **AI Engine**: Google Gemini API (google-genai)
- **Testing**: pytest

---

## System Architecture

The project follows a **Deterministic-First, AI-Assisted** architecture. Instead of passing an entire `.zip` payload directly to an LLM, the system processes it in layers:

1. **Extraction Layer**: Securely unpacks the ZIP, explicitly filtering out and ignoring binaries, media, and heavy dependencies (`node_modules`, `.venv`) before they are even written to disk. This prevents path traversal, Zip Slip attacks, and runaway disk usage.
2. **Analysis Layer (Scanner)**: A deterministic static analysis engine that parses the code to extract factual project evidence (languages, frameworks, dependencies, and directory structure).
3. **AI Reasoning Engine**: Passes only the lightweight, normalized project *evidence* to the Gemini API. The AI generates interview questions, infers skills, and evaluates project outcomes based strictly on this factual evidence.

This layered approach minimizes LLM hallucinations, drastically reduces token usage and API costs, and ensures that every AI-generated conclusion is fully grounded in verifiable codebase facts.

---

## Installation & Setup

1. **Create and Activate a Virtual Environment**:
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # macOS/Linux:
   source .venv/bin/activate
   ```

2. **Install Dependencies**:
   Ensure `requirements.txt` is populated with backend dependencies:
   ```text
   fastapi==0.138.1
   uvicorn==0.49.0
   pydantic==2.13.4
   pydantic-settings==2.14.2
   google-genai==2.10.0
   python-multipart==0.0.32
   python-dotenv==1.2.2
   pytest==9.1.1
   httpx==0.28.1
   ```
   Install them:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create a `.env.local` file (or copy `.env.example`) to configure settings:
   ```env
   # Application Metadata
   APP_NAME="Project Submission AI Analyzer"
   APP_VERSION=1.0.0
   API_VERSION=v1
   DEBUG=false
   ENVIRONMENT=development

   # Logging
   LOG_LEVEL=INFO

   # AI Provider Configurations
   AI_PROVIDER=gemini
   GEMINI_API_KEY="YOUR_GEMINI_API_KEY"
   DEFAULT_MODEL=gemini-2.5-flash
   REQUEST_TIMEOUT_SECONDS=60

   # Upload and Extraction Limits
   MAX_UPLOAD_SIZE_MB=100
   MAX_EXTRACTION_FILES=5000
   MAX_FILE_SIZE_MB=10
   ```

---

## Running the Application

Start the FastAPI application locally using Uvicorn:
```bash
uvicorn app.main:app --reload --port 8000
```
- **API Endpoint**: `http://localhost:8000/api/v1/analyze-submission`
- **Interactive Documentation (Swagger UI)**: `http://localhost:8000/docs`
- **Alternative Documentation (ReDoc)**: `http://localhost:8000/redoc`

---

## Testing with Postman

A ready-to-import Postman collection is included at `postman/AI_Analyzer.postman_collection.json`.

### Import Steps
1. Open **Postman**.
2. Click **Import** (top-left).
3. Drag and drop `postman/AI_Analyzer.postman_collection.json` onto the import dialog, or click **Browse** and select the file.
4. The collection **"Project Submission AI Analyzer"** will appear in your sidebar.

### Sending the Analyze Submission Request

1. Open the **"Analyze Submission – Full Request"** request.
2. Go to the **Body** tab → select **form-data**.
3. Fill in the fields:

| Key | Type | Required | Description |
|-----|------|----------|-------------|
| `project_title` | Text | ✅ Yes | Project title (max 200 chars) |
| `project_description` | Text | No | Short description (max 5000 chars) |
| `project_outcomes` | Text | ✅ Yes | Newline or comma separated objectives |
| `questions_per_skill` | Text | No | Integer 1–5 (default: 2) |
| `zip_file` | **File** | ✅ Yes | Your `.zip` project archive |

4. For `zip_file`: click the **Type** dropdown on the right of the key name and select **File**, then click **Select Files** to choose your `.zip` archive.
5. Click **Send**.

### Example Successful Response (200 OK)
```json
{
  "project_title": "Inventory Management System",
  "suggested_skills": [
    { "skill_id": "sk-py-001", "skill_name": "Python", "confidence": 0.95, "rationale": "Python detected in 100% of source files." },
    { "skill_id": "sk-fw-fastapi", "skill_name": "FastAPI", "confidence": 0.90, "rationale": "FastAPI imports detected in main.py." }
  ],
  "evaluation_report": {
    "skills": [{ "skill_id": "sk-py-001", "skill_name": "Python", "confidence": 0.95, "rationale": "Primary language." }],
    "summary": {
      "overall_alignment": "strong",
      "alignment_score": 0.90,
      "narrative": "The submission demonstrates strong alignment with all stated objectives.",
      "strengths": ["REST API implemented", "Unit tests present"],
      "gaps": []
    },
    "outcome_evaluation": [
      { "stated_outcome": "Build REST API", "status": "met", "evidence": "GET /items and POST /items detected in routes.py.", "gap": null }
    ]
  },
  "viva_questions": [
    {
      "skill_id": "sk-py-001",
      "skill_name": "Python",
      "question_type": "conceptual",
      "question": "What is the difference between a list and a tuple in Python?",
      "expected_answer_hint": "Lists are mutable; tuples are immutable."
    },
    {
      "skill_id": "sk-fw-fastapi",
      "skill_name": "FastAPI",
      "question_type": "codebase",
      "question": "In your routes.py, why did you use async def for route handlers?",
      "expected_answer_hint": "FastAPI supports async for non-blocking I/O."
    }
  ],
  "metadata": {
    "files_analyzed": 24,
    "source_files": 18,
    "processing_time_ms": 47,
    "parser_version": "1.0",
    "model": "gemini-2.5-flash"
  },
  "processing_time_ms": 3420
}
```

> **Note**: `viva_questions` are AI-generated by Gemini and require `GEMINI_API_KEY` to be set in `.env.local`.

### Common Error Codes

| HTTP Status | `code` field | Cause |
|-------------|-------------|-------|
| `400` | `INVALID_ZIP` | Corrupt ZIP, path traversal, or bomb detection |
| `413` | `FILE_TOO_LARGE` | Upload exceeds `MAX_UPLOAD_SIZE_MB` limit |
| `415` | `UNSUPPORTED_ARCHIVE` | File extension is not `.zip` |
| `422` | `VALIDATION_ERROR` | Missing/invalid form fields |
| `500` | `CATALOG_MISSING` | `skills/skills_catalog.json` file is missing |
| `502` | `AI_PARSE_ERROR` | Gemini returned malformed JSON |
| `503` | `SERVICE_UNAVAILABLE` | `GEMINI_API_KEY` not configured in `.env.local` |
| `504` | `AI_TIMEOUT` | Gemini request exceeded timeout limit |

---

## Running API Calls Manually (CLI)

### 1. Using curl (macOS / Linux / Git Bash)
```bash
curl -X POST "http://localhost:8000/api/v1/analyze-submission" \
  -F "project_title=Inventory Management System" \
  -F "project_description=REST API built with FastAPI and SQLite" \
  -F "project_outcomes=1. Build REST API, 2. Implement SQLite DB" \
  -F "questions_per_skill=2" \
  -F "zip_file=@/path/to/your/project.zip"
```

### 2. Using PowerShell (Windows)
```powershell
$uri = "http://localhost:8000/api/v1/analyze-submission"
$zipPath = "C:\absolute\path\to\your\project.zip"

$form = @{
    project_title = "Inventory Management System"
    project_description = "REST API built with FastAPI and SQLite"
    project_outcomes = "1. Build REST API, 2. Implement SQLite DB"
    questions_per_skill = "2"
    zip_file = Get-Item -Path $zipPath
}

Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

---

## Testing & Verification

The project is fully covered by a robust test suite (75 passing tests) ensuring API stability, secure file processing, and robust AI parsing.

### What is Verified?
- **Security Tests**: Ensures the `ZipExtractor` rejects excessively large files, prevents path traversal attacks, handles corrupt archives gracefully, and strictly skips ignored directories.
- **Scanner Tests**: Validates that the deterministic project scanner correctly infers languages, frameworks, and dependencies without throwing errors.
- **AI Service Tests**: Mocks the Gemini API to verify that the system correctly builds prompts, parses the resulting structured JSON, and strictly enforces the `skills_catalog.json` schema.
- **API Tests**: Tests FastAPI endpoints, request validation, payload limits, and HTTP error handling.

To run the full test suite:
```bash
pytest
```
Or run with verbose output:
```bash
pytest -v
```

---

## Performance & Optimization

To ensure fast and cost-effective analysis, the system includes built-in optimizations:
- **Smart Directory Pruning**: Common heavy dependency directories (e.g., `node_modules`, `.venv`, `venv`, `.git`) are explicitly ignored during both ZIP extraction and static codebase analysis.
- **Pre-Extraction Filtering**: Files belonging to ignored directories or with unsupported extensions (e.g., binaries, media files) are filtered out *before* they are even extracted to disk. This heavily reduces unnecessary disk I/O and temporary storage footprint.
- **Selective Processing**: By skipping unneeded environment files and focusing only on source code logic, the system saves API tokens and avoids unnecessary AI processing time.
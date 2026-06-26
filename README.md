# AI Submission Analyzer

A FastAPI service that analyzes intern/student project ZIP submissions and returns a mentor-ready evaluation report.

## What it does

Upload a project ZIP + metadata → get back a JSON report with:

- **Skill Detection** — detected skills with confidence scores and code evidence snippets
- **Viva Questions** — conceptual + codebase-specific questions per detected skill
- **Outcome Evaluation** — did the student deliver what they claimed?
- **Tech Stack Detection** — languages, frameworks, and dependency files detected
- **Security Scan** — static analysis for hardcoded credentials, dangerous patterns, and more

A built-in **web frontend** (served at `/`) lets you submit projects and read reports without any API client.

## Project Structure

```
ai-submission-analyzer/
├── app/
│   ├── main.py                    # FastAPI app entry point (CORS, static files, lifespan)
│   ├── api/routes.py              # POST /api/v1/analyze-submission
│   ├── core/
│   │   ├── config.py              # Pydantic settings from .env
│   │   └── logging_config.py      # Structured JSON logging
│   ├── models/schemas.py          # Pydantic request/response models
│   ├── services/
│   │   ├── zip_extractor.py       # Secure ZIP extraction
│   │   ├── code_sanitizer.py      # Static security scanner
│   │   ├── project_scanner.py     # File tree builder + content reader
│   │   ├── tech_detector.py       # Language/framework detection
│   │   ├── context_builder.py     # CAG context assembly
│   │   ├── skill_matcher.py       # Skill matching against catalog
│   │   ├── question_generator.py  # LLM viva question generation
│   │   ├── outcome_evaluator.py   # LLM outcome evaluation
│   │   └── report_generator.py    # Final report assembly
│   ├── llm/
│   │   ├── base.py                # Abstract LLM interface
│   │   ├── gemini_client.py       # Google Gemini API (with API key rotation)
│   │   ├── local_llm_client.py    # Ollama / LM Studio
│   │   └── llm_factory.py         # Provider selection
│   └── data/skills_catalog.json   # Local skill definitions
├── static/
│   └── index.html                 # Built-in web frontend
└── tests/                         # Pytest test suite (6 modules)
```

## Setup

```bash
# 1. Clone and enter the project
cd ai-submission-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set your GEMINI_API_KEYS (or switch to local LLM)

# 4. Run the server
uvicorn app.main:app --reload
```

The server starts at `http://localhost:8000`.

| URL | Description |
|---|---|
| `http://localhost:8000` | Built-in web frontend |
| `http://localhost:8000/docs` | Swagger UI |
| `http://localhost:8000/health` | Health check |

## Configuration (`.env`)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` or `local` |
| `GEMINI_API_KEYS` | — | Comma-separated Gemini API keys — rotated automatically on quota/rate-limit |
| `GEMINI_MODEL` | `gemini-2.0-flash` | Gemini model name |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434` | Ollama / LM Studio base URL |
| `LOCAL_LLM_MODEL` | `llama3` | Local model name |
| `MAX_ZIP_SIZE_MB` | `50` | Max uploaded ZIP size (compressed) |
| `MAX_UNCOMPRESSED_SIZE_MB` | `500` | Zip bomb protection — max total uncompressed size |
| `MAX_FILE_COUNT` | `1000` | Max number of files in the ZIP |
| `MAX_SINGLE_FILE_SIZE_MB` | `1` | Max size of any single extracted file |
| `DEFAULT_QUESTIONS_PER_SKILL` | `3` | Questions generated per skill (1–10) |
| `CONFIDENCE_THRESHOLD` | `0.3` | Skills below this score are flagged as low-confidence |
| `LOG_LEVEL` | `INFO` | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) |

> **Tip:** Supply multiple keys (`GEMINI_API_KEYS=key1,key2,key3`) to enable automatic rotation when a key hits its quota.

## API

### `POST /api/v1/analyze-submission`

Accepts a `multipart/form-data` request.

**Form fields:**

| Field | Type | Required | Description |
|---|---|---|---|
| `zip_file` | File | ✅ | The project ZIP archive |
| `project_title` | string | ✅ | Project name (max 200 chars) |
| `project_description` | string | ✅ | What the project does (10–5000 chars) |
| `project_outcomes` | string | ✅ | What the student aimed to achieve (10–5000 chars) |
| `questions_per_skill` | int | ❌ | Questions per skill (default `3`, range 1–10) |

**Response:** `AnalysisResponse` JSON object:

```jsonc
{
  "project_title": "...",
  "suggested_skills": [
    {
      "skill": {
        "skill_id": "...",
        "skill_name": "...",
        "confidence": 0.85,
        "low_confidence": false,
        "rationale": "...",
        "evidence": [{ "file_path": "...", "snippet": "..." }]
      },
      "questions": [
        {
          "question_text": "...",
          "question_focus": "conceptual",   // or "codebase"
          "expected_key_points": ["..."]
        }
      ]
    }
  ],
  "evaluation_report": {
    "strengths": ["..."],
    "gaps": ["..."],
    "summary": "...",
    "outcome_evaluations": [
      { "stated_outcome": "...", "is_met": true, "confidence": 0.9, "evidence": "...", "gaps": [] }
    ]
  },
  "tech_detection": {
    "languages": ["Python"],
    "frameworks": ["FastAPI"],
    "dependencies": ["..."],
    "dependency_files_found": ["requirements.txt"]
  },
  "security_scan": {
    "flags": [
      { "file_path": "...", "line_number": 42, "pattern": "hardcoded_secret", "severity": "high", "description": "..." }
    ],
    "has_high_severity": false,
    "summary": "..."
  },
  "metadata": {
    "files_analyzed": 12,
    "skipped_files": 2,
    "extraction_time_ms": 45.2,
    "analysis_time_ms": 3210.5,
    "model_tokens_used": 8400,
    "llm_provider": "gemini"
  },
  "processing_time_ms": 3255.7,
  "analysis_note": null
}
```

### `GET /health`

Returns service liveness, version, and active LLM provider.

### `GET /docs`

Interactive Swagger UI for the full API.

## Security Protections

| Threat | Protection |
|---|---|
| Path traversal (`../../../etc/passwd`) | Every ZIP member path validated against the temp directory before extraction |
| Zip bomb | Uncompressed size + file count checked from ZIP metadata **before** extraction |
| Dangerous file types (`.exe`, `.sh`, `.bat`, `.ps1` …) | Blocked extension list — files are skipped, never extracted |
| Oversized single files | Per-file size limit (`MAX_SINGLE_FILE_SIZE_MB`) enforced during extraction |
| Symlink escape | Unix symlink attribute check — symlinks are always skipped |
| Malicious code execution | Uploaded code is **never executed** — read-only static analysis only |
| Hardcoded credentials / private keys | Detected by `code_sanitizer`, flagged with severity in report |
| OS command injection in code | Dangerous patterns (`subprocess`, `os.system`, `eval`, `exec`) detected and flagged |
| Temp directory leakage | Every extraction uses `tempfile.mkdtemp()`, cleaned up in a guaranteed `finally` block |

## Running Tests

```bash
python -m pytest tests/ -v
```

The test suite covers:

| Module | Coverage |
|---|---|
| `test_api.py` | Endpoint integration tests |
| `test_zip_extractor.py` | ZIP security edge cases |
| `test_skill_matcher.py` | Skill detection and confidence scoring |
| `test_tech_detector.py` | Language and framework detection |
| `test_code_sanitizer.py` | Security pattern detection |
| `test_outcome_evaluator.py` | LLM outcome evaluation logic |

## Extending the Skill Catalog

Edit `app/data/skills_catalog.json` to add new skills:

```json
{
  "skill_id": "my_skill",
  "skill_name": "My Skill Name",
  "keywords": ["keyword1", "keyword2"],
  "frameworks": ["Framework Name"],
  "file_extensions": [".py", ".js"]
}
```

## Architecture Notes

- **CAG (Context-Augmented Generation):** Project context is built once per request and reused across all LLM prompts — no vector database required.
- **Pluggable LLM:** An abstract base class (`llm/base.py`) supports Google Gemini (with key rotation) and local models via Ollama / LM Studio.
- **No persistent storage:** Stateless by design — no database, no auth, no file retention between requests.
- **Static frontend:** A single-page `index.html` is served from `/static/` and accessible at the root URL.

## Tech Stack

| Layer | Technology |
|---|---|
| Runtime | Python 3.12+ |
| Web framework | FastAPI + Uvicorn |
| Data validation | Pydantic v2 |
| AI / LLM | Google Gemini (`gemini-2.0-flash`) or Ollama / LM Studio |
| Testing | Pytest + pytest-asyncio |
| HTTP client | httpx |

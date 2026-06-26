# AI Submission Analyzer

A FastAPI service that analyzes intern/student project ZIP submissions and returns a mentor-ready evaluation report.

## What it does

Upload a project ZIP + metadata → get back a JSON report with:
- Detected skills with confidence scores and code evidence
- Conceptual + codebase-specific viva questions per skill
- Outcome evaluation (did the student deliver what they claimed?)
- Technology stack detection
- Security scan of the submitted code

## Project Structure

```
ai-submission-analyzer/
├── app/
│   ├── main.py                    # FastAPI app entry point
│   ├── api/routes.py              # POST /api/v1/analyze-submission
│   ├── core/
│   │   ├── config.py              # Settings from .env
│   │   └── logging_config.py     # Structured JSON logging
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
│   │   ├── gemini_client.py       # Google Gemini API
│   │   ├── local_llm_client.py    # Ollama / LM Studio
│   │   └── llm_factory.py         # Provider selection
│   └── data/skills_catalog.json   # Local skill definitions
└── tests/                         # Pytest test suite
```

## Setup

```bash
# 1. Clone and enter the project
cd ai-submission-analyzer

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and set your GEMINI_API_KEY (or switch to local LLM)

# 4. Run the server
uvicorn app.main:app --reload
```

## Configuration (.env)

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `gemini` | `gemini` or `local` |
| `GEMINI_API_KEY` | — | Required if using Gemini |
| `GEMINI_MODEL` | `gemini-1.5-flash` | Gemini model name |
| `LOCAL_LLM_BASE_URL` | `http://localhost:11434` | Ollama/LM Studio URL |
| `LOCAL_LLM_MODEL` | `llama3` | Local model name |
| `MAX_ZIP_SIZE_MB` | `50` | Max uploaded ZIP size |
| `MAX_UNCOMPRESSED_SIZE_MB` | `500` | Zip bomb protection limit |
| `MAX_FILE_COUNT` | `1000` | Max files in ZIP |
| `DEFAULT_QUESTIONS_PER_SKILL` | `3` | Questions generated per skill |
| `CONFIDENCE_THRESHOLD` | `0.3` | Below this = low confidence flag |

## API

### POST /api/v1/analyze-submission

**Form fields:**
- `project_title` (string) — project name
- `project_description` (string) — what the project does
- `project_outcomes` (string) — what the student aimed to achieve
- `questions_per_skill` (int, default 3) — questions to generate per skill
- `zip_file` (file) — the project ZIP archive

**Response:** JSON report with skills, questions, evaluation, security scan, metadata.

### GET /health
### GET /docs  (Swagger UI)

## Security Protections

| Threat | Protection |
|---|---|
| Path traversal (../../../etc) | Every ZIP member path validated before extraction |
| Zip bomb | Uncompressed size + file count checked from metadata before extraction |
| Dangerous file types (.exe, .sh, .bat, .ps1...) | Blocked extension list — never extracted |
| Symlink escape | Unix symlink attribute check — symlinks skipped |
| Malicious code execution | Code is NEVER executed — read-only static analysis only |
| Hardcoded credentials | Detected by code_sanitizer, flagged in report |
| OS command injection in code | Detected patterns: subprocess, os.system, eval, exec |
| Temp directory leakage | All extractions use `tempfile.mkdtemp()`, cleaned in `finally` block |

## Running Tests

```bash
python -m pytest tests/ -v
```

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

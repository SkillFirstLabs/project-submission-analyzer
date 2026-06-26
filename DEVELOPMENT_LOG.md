# AI Submission Analyzer — Full Development Log

**Project:** AI Submission Analyzer — Phase 1 MVP  
**Stack:** Python 3.14, FastAPI, Pydantic, Gemini AI / LM Studio (Qwen 3.5 9B)  
**Server:** `http://localhost:8000`  
**Frontend:** `http://localhost:8000` (served from `/static/index.html`)  
**API Docs:** `http://localhost:8000/docs`

---

## Overview

A FastAPI service that accepts a student project ZIP file + metadata, runs a full static analysis pipeline, and returns a mentor-ready JSON evaluation report containing:

- Detected skills with confidence scores and code evidence
- Conceptual and codebase-specific viva questions per skill
- Outcome evaluation (stated goals vs actual code)
- Technology stack detection
- Static security scan of submitted code

---

## Session 1 — Requirements & Planning

### Source Documents Read
All 6 specification documents in `Document/` were reviewed:

| File | Contents |
|---|---|
| `01_Product_Requirements_Document.md` | Goal, scope, out-of-scope, AI strategy (CAG pipeline) |
| `02_Software_Requirements_Specification.md` | FR-001 to FR-015, non-functional requirements |
| `03_Technical_Requirements_Document.md` | Stack, 10 modules, CAG definition |
| `04_System_Design_Document.md` | Linear pipeline diagram, 5 core components |
| `05_API_Design_Document.md` | Single endpoint spec, inputs, outputs, error codes |
| `06_Data_Model_Document.md` | Project, Skill, Question, Evaluation, Metadata models |
| `Project Submission AI Analyzer - Task.pdf` | Full task brief including grading rubric |

### Architecture Decisions Made
- **CAG (Context-Augmented Generation):** Build project context once per request, reuse across all LLM prompts — no vector DB
- **No code execution:** Read-only static analysis only — defence-in-depth security
- **Pluggable LLM:** Abstract base class supports Gemini API and local LLM (LM Studio/Ollama)
- **Skill catalog:** Local JSON file — no external database
- **No auth/DB/persistent storage** as per PRD out-of-scope

---

## Session 2 — Security Discussion

### Threats Identified and Resolved

| Threat | Resolution |
|---|---|
| Path traversal (`../../../etc/passwd`) | Resolve every ZIP member path, check it stays inside temp dir |
| Zip bomb (tiny compressed, huge uncompressed) | Check uncompressed size + file count from ZIP metadata before extraction |
| Malicious file types (`.exe`, `.sh`, `.bat`, `.ps1`) | Blocked extension list — files skipped, never extracted |
| Symlink escape | Unix file attribute check — symlinks skipped |
| Malicious code gaining filesystem access | Code is **never executed** — only read as text for analysis |
| Hardcoded credentials / private keys | Static pattern scanner flags them in report |
| `eval()`, `exec()`, `subprocess` in uploaded code | Code sanitizer detects and flags — does not execute |
| Temp dir leakage between requests | `tempfile.mkdtemp()` + guaranteed cleanup in `finally` block |

### Decision on Docker Sandbox
Docker sandbox (full code execution isolation) confirmed as **Phase 2 / post-MVP** per PRD. Phase 1 protection: never execute uploaded code + static pattern scanning.

---

## Session 3 — Full Build (Phase 1 MVP)

### Project Structure Created

```
ai-submission-analyzer/
├── app/
│   ├── main.py                      # FastAPI app, CORS, static files, lifespan
│   ├── api/
│   │   └── routes.py                # POST /api/v1/analyze-submission
│   ├── core/
│   │   ├── config.py                # Pydantic settings from .env
│   │   └── logging_config.py        # Structured JSON logging
│   ├── models/
│   │   └── schemas.py               # All Pydantic request/response models
│   ├── services/
│   │   ├── zip_extractor.py         # Secure ZIP extraction
│   │   ├── code_sanitizer.py        # Static security scanner
│   │   ├── project_scanner.py       # File tree builder + content reader
│   │   ├── tech_detector.py         # Language/framework/dependency detection
│   │   ├── context_builder.py       # CAG context assembly
│   │   ├── skill_matcher.py         # Deterministic skill matching
│   │   ├── question_generator.py    # LLM viva question generation
│   │   ├── outcome_evaluator.py     # LLM outcome evaluation
│   │   └── report_generator.py      # Final report assembly
│   ├── llm/
│   │   ├── base.py                  # Abstract LLM interface
│   │   ├── gemini_client.py         # Google Gemini with 5-key rotation
│   │   ├── local_llm_client.py      # LM Studio / Ollama client
│   │   └── llm_factory.py           # Provider singleton factory
│   └── data/
│       └── skills_catalog.json      # 50-skill catalog
├── static/
│   └── index.html                   # Immersive testing frontend
├── tests/
│   ├── test_zip_extractor.py        # 8 tests
│   ├── test_code_sanitizer.py       # 10 tests
│   ├── test_skill_matcher.py        # 8 tests
│   └── test_tech_detector.py        # 7 tests
├── .env                             # Active config (not committed)
├── .env.example                     # Config template
├── requirements.txt
└── README.md
```

### Every File — What It Does

#### `app/main.py`
- FastAPI app entry point
- CORS middleware (allows all origins for local dev)
- Mounts `/static` directory to serve the frontend
- Startup: validates skill catalog exists and logs provider info
- Registers `/api/v1` router and `/health` endpoint
- Serves `index.html` at `/`

#### `app/api/routes.py`
- Single endpoint: `POST /api/v1/analyze-submission`
- Form fields: `project_title`, `project_description`, `project_outcomes`, `questions_per_skill`, `llm_provider` (override), `zip_file`
- Full pipeline orchestration: extract → scan → security → tech → context → skills → LLM → report
- Guaranteed temp dir cleanup in `finally` block
- Structured error handling: 400, 413, 422, 500

#### `app/core/config.py`
- Pydantic `BaseSettings` loaded from `.env`
- Settings: `LLM_PROVIDER`, `GEMINI_API_KEYS` (comma-separated), `GEMINI_MODEL`, `LOCAL_LLM_BASE_URL`, `LOCAL_LLM_MODEL`, upload limits, confidence threshold
- `gemini_api_key_list` property splits comma-separated keys
- `@lru_cache` singleton with `clear_settings_cache()` helper

#### `app/core/logging_config.py`
- `JSONFormatter`: every log line is a single JSON object with timestamp, level, logger, message, module, function, line
- `setup_logging()` configures root logger at startup
- Note: avoids reserved `LogRecord` keys (`filename`, `module`, `message`, etc.) in `extra={}` dicts

#### `app/models/schemas.py`
All Pydantic v2 models:
- `AnalysisRequest` — form input validation
- `ProjectMetadata`, `FileNode`, `ProjectTree` — scan results
- `TechDetectionResult` — languages, frameworks, dependencies
- `SecurityFlag`, `SecurityScanResult` — security scan output
- `DetectedSkill` with `confidence`, `low_confidence` flag, `evidence`
- `Question` with `question_focus` (conceptual/codebase) and `expected_key_points`
- `SkillWithQuestions` — skill + its questions
- `OutcomeEvaluation`, `EvaluationReport` — outcome analysis
- `ReportMetadata` — files analyzed, timing, tokens, provider
- `AnalysisResponse` — final JSON response with `analysis_note`
- `ErrorResponse` — structured error format

#### `app/services/zip_extractor.py`
Security protections:
1. Magic bytes check — validates real ZIP before doing anything
2. **Zip bomb check** — reads uncompressed size + file count from metadata (before extraction); raises `ZIP_BOMB_DETECTED` or `ZIP_TOO_MANY_FILES`
3. Creates `tempfile.mkdtemp()` — isolated temp directory
4. **Path traversal check** — every member path resolved and checked to be inside temp dir
5. **Symlink check** — Unix file attribute bits checked; symlinks skipped
6. **Extension blocklist** — `.exe`, `.sh`, `.bat`, `.ps1`, `.dll`, `.bin`, etc. never extracted
7. **Allowed extension list** — only source/config files extracted
8. **Per-file size check** — enforced both from metadata and during streaming write
9. Streaming extraction in 64KB chunks
10. `ExtractionResult.cleanup()` — `shutil.rmtree` in finally, always runs

#### `app/services/code_sanitizer.py`
- Pure static pattern scanner — **never executes code**
- Separate pattern sets for Python, JavaScript/TypeScript, and general (all files)
- **High severity:** `eval()`, `exec()`, `subprocess`, `os.system`, `pickle.loads`, `ctypes`, `/etc/passwd`, hardcoded credentials, private keys, path traversal opens
- **Medium severity:** file system modification, absolute path opens, raw sockets, `yaml.load` without Loader
- **Low severity:** outbound HTTP requests, localhost references, environment variable access
- Returns `SecurityScanResult` with all flags, `has_high_severity` bool, and summary
- Never raises on any input (try/except around every file scan)

#### `app/services/project_scanner.py`
- Walks extracted temp dir with `os.walk`
- Prunes ignored dirs: `__pycache__`, `node_modules`, `.git`, `.venv`, etc.
- Maps file extensions to language names (30+ extensions)
- Reads files as UTF-8, falls back to latin-1, skips binaries
- Skips files over `max_single_file_size_bytes`
- Returns `ScanResult` with `ProjectTree` + `file_contents` dict

#### `app/services/tech_detector.py`
- 35+ framework/library signatures (regex against file content)
- Covers: FastAPI, Flask, Django, React, Next.js, Vue, Angular, Express, Spring Boot, scikit-learn, TensorFlow, PyTorch, Pandas, NumPy, LangChain, SQLAlchemy, Mongoose, Prisma, and more
- Parses dependency files: `requirements.txt`, `package.json`, `pyproject.toml`, `pom.xml`, `build.gradle`, `Cargo.toml`
- Language detection by extension, sorted by frequency (most-used first)

#### `app/services/context_builder.py`
- Assembles the CAG context string (built once, reused for all LLM prompts)
- Sections: project overview, tech summary, file tree (capped at 50 files), key file contents
- Files sorted by priority (Python/JS first, config after)
- Per-file truncation at 3000 chars, total context cap at 40000 chars
- Never sends full codebase to LLM — smart truncation

#### `app/services/skill_matcher.py`
- Loads `skills_catalog.json` at call time (validates existence and non-empty)
- For each catalog skill: checks if any relevant file extensions exist, counts keyword hits across all files, checks framework matches
- Confidence scoring: log-scale keyword hits (0–0.75) + framework boost (0.25) = 0.0–1.0
- Collects code evidence snippets (file path + line)
- Flags skills below `CONFIDENCE_THRESHOLD` as `low_confidence`
- **Graceful handling:** empty files → note; no skills matched → note; catalog missing → note; all low confidence → note
- Returns sorted by confidence descending

#### `app/services/question_generator.py`
- **Parallel execution via `asyncio.gather()`** — all skills processed simultaneously
- Caps at top 5 skills by confidence (keeps local LLM load manageable)
- Prompt uses `.replace()` instead of `.format()` — prevents `KeyError` from `{` and `}` in uploaded source code
- Parses LLM response: extracts JSON array from anywhere in the response (handles preamble text)
- **Fallback:** 3 template-based questions per skill when LLM fails or returns empty

#### `app/services/outcome_evaluator.py`
- Sends full CAG context + stated outcomes to LLM
- Asks for structured JSON: strengths, gaps, summary, per-outcome evaluation (is_met, confidence, evidence, gaps)
- **Fallback:** keyword-based matching when LLM unavailable — checks if outcome words appear in codebase
- Parses JSON from LLM response with regex extraction

#### `app/services/report_generator.py`
- Assembles `AnalysisResponse` from all pipeline outputs
- Combines skill matcher note + security warning into `analysis_note`
- Records all timing: extraction_ms, analysis_ms, total processing_ms

#### `app/llm/base.py`
Abstract interface: `generate(prompt, system_prompt) -> LLMResponse`, `is_available() -> bool`

#### `app/llm/gemini_client.py`
- Holds list of all 5 API keys
- Thread-safe key rotation using `threading.Lock`
- Rotates on: `ResourceExhausted` (429), `ServiceUnavailable`, `PermissionDenied`, `Unauthenticated`
- Tries every key before giving up
- Non-rotatable errors (content policy, bad prompt) fail immediately

#### `app/llm/local_llm_client.py`
- **Primary:** OpenAI-compatible `/v1/chat/completions` (LM Studio format)
- **Fallback:** Ollama `/api/generate`
- **Reasoning model support (Qwen 3, DeepSeek-R1):** `_extract_text()` function handles models that return empty `content` and put the answer in `reasoning_content`; also strips `<think>...</think>` inline blocks
- `max_tokens: 4096` — enough for thinking preamble + actual answer
- Timeout: 300s (5 min) for slow local inference

#### `app/llm/llm_factory.py`
- Per-provider singleton cache (`_clients` dict)
- `get_llm_client()` — returns default from settings
- `get_llm_client_for_provider(provider)` — per-request override
- `reset_llm_client()` — clears cache for config changes

#### `app/data/skills_catalog.json`
50 skills from the official task catalog, enriched with:
- `keywords` — code patterns to search for
- `frameworks` — framework names that boost confidence
- `file_extensions` — which file types to search

Categories: Programming Language, Frontend, Backend, Database, Cloud, DevOps, Data & AI, Mobile, Security

#### `static/index.html`
Single-file immersive frontend:
- Animated particle canvas background (WebGL-less, pure Canvas 2D)
- **LLM toggle** — Gemini AI vs Local LLM, synced between nav and form bar
- Live status dot — checks LM Studio `/v1/models` on toggle
- **Quick Fill presets** — FastAPI, ML, React, Full Stack sample data
- Drag & drop ZIP upload with file validation
- Questions per skill slider (1–10)
- Animated step-by-step progress tracker (visual simulation)
- Results wait for actual API fetch — no premature timeout
- **6 result tabs:** Skills, Evaluation, Tech Stack, Security, Metadata, Raw JSON
- Skill cards: expandable, confidence bar, evidence chips, colour-coded questions
- Outcome evaluation: strengths/gaps grid, per-outcome status with confidence
- Security flags: severity badges (high/red, medium/yellow, low/green)
- JSON tab: syntax highlighted, copy to clipboard, download as file
- Toast notifications for all user actions

---

## Session 4 — Skills Catalog Update

Replaced internal skills catalog with the official 50-skill task catalog:

```
sk-001 Python          sk-018 FastAPI         sk-034 Docker
sk-002 Java            sk-019 Django          sk-035 Kubernetes
sk-003 JavaScript      sk-020 Flask           sk-036 CI/CD
sk-004 TypeScript      sk-021 Spring Boot     sk-037 Git
sk-005 C++             sk-022 REST API Design sk-038 Linux
sk-006 C#              sk-023 GraphQL         sk-039 Terraform
sk-007 Go              sk-024 PostgreSQL      sk-040 Nginx
sk-008 Kotlin          sk-025 MySQL           sk-041 Machine Learning
sk-009 React           sk-026 MongoDB         sk-042 Data Analysis
sk-010 Angular         sk-027 Redis           sk-043 Pandas
sk-011 Vue.js          sk-028 SQLite          sk-044 NumPy
sk-012 Next.js         sk-029 SQL             sk-045 TensorFlow
sk-013 HTML/CSS        sk-030 AWS             sk-046 PyTorch
sk-014 Tailwind CSS    sk-031 Microsoft Azure sk-047 React Native
sk-015 Responsive Web  sk-032 Google Cloud    sk-048 Flutter
sk-016 Node.js         sk-033 Firebase        sk-049 Android Dev
sk-017 Express.js                             sk-050 Cybersecurity
```

Each skill enriched with detection keywords, framework names, and file extensions.

---

## Session 5 — LM Studio Integration

### Connection Details
- **URL:** `http://127.0.0.1:1234`
- **Model:** `qwen/qwen3.5-9b`
- **Endpoint used:** `POST /v1/chat/completions` (OpenAI-compatible)

### Changes Made
- Updated `.env`: `LLM_PROVIDER=local`, `LOCAL_LLM_BASE_URL=http://127.0.0.1:1234`, `LOCAL_LLM_MODEL=qwen/qwen3.5-9b`
- Added per-request `llm_provider` form field so frontend toggle switches provider without server restart
- LLM factory updated to maintain separate singletons per provider

---

## Session 6 — Per-Request LLM Toggle (Frontend + Backend)

### Backend
- Added `llm_provider: Optional[str]` form field to `POST /analyze-submission`
- `get_llm_client_for_provider(provider)` function in factory
- Both Gemini and Local LLM singletons cached independently

### Frontend
- Nav-level mini toggle (Gemini / Local)
- Full-width provider bar in form with live status dot
- Submit button text updates to reflect active provider
- Status dot checks LM Studio `/v1/models` health on switch

---

## Session 7 — Bug Fixes

### Bug 1: Server crashed on every request
**Root cause:** `extra={"filename": ...}` in `logger.info()` — `filename` is a reserved key in Python's `logging.LogRecord`. Passing it via `extra={}` raises `KeyError` immediately before any analysis runs.  
**Fix:** Renamed to `"zip_filename"`.

### Bug 2: Viva question generation always failed
**Root cause:** `_QUESTION_PROMPT_TEMPLATE.format(...)` was called with `context_excerpt` and `evidence` strings that contain literal `{` and `}` characters from uploaded source code (Python dicts, JS objects, etc.). Python's `str.format()` interprets those as format tokens and raises `KeyError`.  
**Fix:** Replaced `.format()` with chained `.replace()` calls — immune to any characters in the content.

### Bug 3: Gemini 404 model not found
**Root cause:** `gemini-1.5-flash` was deprecated from the `v1beta` API.  
**Fix:** Updated model to `gemini-2.0-flash` in `.env`.

### Bug 4: UI showed "no results" even when API succeeded
**Root cause:** Frontend had a `setTimeout(6000)` that fired after 6 seconds and tried to render results. With Qwen 3.5 taking 2+ minutes per call, the timer fired while the API was still running — rendering an empty/failed state.  
**Fix:** Removed the timer entirely. Results render only when the actual `fetch()` promise resolves. Visual progress steps show `⏳ Waiting for LLM response…` after completing so the user knows it's still working.

### Bug 5: Reasoning model (Qwen 3.5) returned empty content
**Root cause:** Qwen 3.5 is a thinking/reasoning model. It puts its reasoning in `reasoning_content` and returns empty `content`. With `max_tokens: 2048` it ran out of tokens mid-think, making both fields empty.  
**Fix:** 
- Raised `max_tokens` to `4096`
- Added `_extract_text()` function: checks `content` first, strips `<think>` blocks, falls back to `reasoning_content`, looks for answer after `Final Answer:` marker

---

## Session 8 — Speed Optimisation (Parallel LLM Calls)

**Problem:** With 6+ matched skills, LLM was called sequentially — one after another. Each call to Qwen takes ~2 minutes = 12+ minutes total.

**Fix:** Replaced sequential `for` loop in `question_generator.py` with `asyncio.gather()`:
- All skills fire simultaneously as concurrent async tasks
- Total wait = slowest single call (not sum of all calls)
- Capped at **top 5 skills** by confidence score — reduces local LLM load without losing meaningful results

---

## Test Suite

32 tests, all passing (`pytest tests/ -v`):

| File | Tests | What's covered |
|---|---|---|
| `test_zip_extractor.py` | 8 | Valid extraction, path traversal block, blocked extensions, invalid ZIP, empty bytes, zip bomb (monkeypatched), cleanup |
| `test_code_sanitizer.py` | 10 | eval/exec/subprocess detection, hardcoded passwords, /etc/passwd, clean file (no false positives), project scan summary, line numbers, never raises on binary input |
| `test_skill_matcher.py` | 8 | Python/FastAPI match, empty files note, no-match note, confidence range 0–1, low confidence flag, sorted by confidence, catalog loads |
| `test_tech_detector.py` | 7 | Python/JS detection, FastAPI/React framework detection, requirements.txt and package.json parsing, empty files, multi-language |

---

## Configuration Reference

`.env` file (do not commit):

```env
LLM_PROVIDER=local                          # gemini | local
GEMINI_API_KEYS=key1,key2,key3,key4,key5   # 5 keys, rotated on quota errors
GEMINI_MODEL=gemini-2.0-flash
LOCAL_LLM_BASE_URL=http://127.0.0.1:1234
LOCAL_LLM_MODEL=qwen/qwen3.5-9b
MAX_ZIP_SIZE_MB=50
MAX_UNCOMPRESSED_SIZE_MB=500
MAX_FILE_COUNT=1000
MAX_SINGLE_FILE_SIZE_MB=1
DEFAULT_QUESTIONS_PER_SKILL=3
CONFIDENCE_THRESHOLD=0.3
LOG_LEVEL=INFO
```

---

## Running the Project

```bash
# Install dependencies
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env — set LLM_PROVIDER and keys

# Start server
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
python -m pytest tests/ -v
```

---

## API Reference

### `POST /api/v1/analyze-submission`

**Form fields:**

| Field | Type | Required | Notes |
|---|---|---|---|
| `project_title` | string | ✅ | 1–200 chars |
| `project_description` | string | ✅ | 10–5000 chars |
| `project_outcomes` | string | ✅ | 10–5000 chars |
| `questions_per_skill` | int | ❌ | 1–10, default 3 |
| `llm_provider` | string | ❌ | `gemini` or `local` — overrides .env |
| `zip_file` | file | ✅ | `.zip`, max 50MB |

**Response shape:**
```json
{
  "project_title": "...",
  "suggested_skills": [
    {
      "skill": {
        "skill_id": "sk-018",
        "skill_name": "FastAPI",
        "confidence": 0.87,
        "low_confidence": false,
        "rationale": "...",
        "evidence": [{"file_path": "app.py:3", "snippet": "from fastapi import FastAPI"}]
      },
      "questions": [
        {
          "question_text": "...",
          "question_focus": "conceptual",
          "expected_key_points": ["...", "..."]
        }
      ]
    }
  ],
  "evaluation_report": {
    "strengths": ["..."],
    "gaps": ["..."],
    "summary": "...",
    "outcome_evaluations": [
      {"stated_outcome": "...", "is_met": true, "confidence": 0.8, "evidence": "...", "gaps": []}
    ]
  },
  "tech_detection": {
    "languages": ["Python"],
    "frameworks": ["FastAPI", "Pydantic"],
    "dependencies": ["fastapi", "uvicorn"],
    "dependency_files_found": ["requirements.txt"]
  },
  "security_scan": {
    "flags": [],
    "has_high_severity": false,
    "summary": "No security concerns detected."
  },
  "metadata": {
    "files_analyzed": 12,
    "skipped_files": 0,
    "extraction_time_ms": 45.2,
    "analysis_time_ms": 8320.1,
    "model_tokens_used": 4821,
    "llm_provider": "local"
  },
  "processing_time_ms": 8412.5,
  "analysis_note": null
}
```

**Error codes:**

| HTTP | Code | Meaning |
|---|---|---|
| 400 | `INVALID_ZIP` | Not a valid ZIP file |
| 400 | `ZIP_BOMB_DETECTED` | Uncompressed size exceeds limit |
| 400 | `ZIP_TOO_MANY_FILES` | File count exceeds limit |
| 400 | `NO_SOURCE_FILES` | No readable source files in ZIP |
| 413 | `FILE_TOO_LARGE` | ZIP exceeds 50MB |
| 422 | `VALIDATION_ERROR` | Missing/invalid form fields |
| 500 | `INTERNAL_ERROR` | Unexpected server error |

---

## What's Out of Scope (Phase 1)

Per the PRD, these are explicitly NOT implemented:
- Authentication or API keys for the service itself
- Application database or persistent storage
- Code execution / Docker sandbox
- Browser automation
- AI agents
- Runtime testing of submitted code

---

## Known Limitations

- Local LLM (Qwen 3.5) is slow — ~2 min per skill even with parallel calls. Use Gemini for faster results.
- `gemini-2.0-flash` requires valid API keys — test with local LLM if keys are exhausted
- Skills capped at top 5 when using local LLM to prevent timeout
- Zip files with Windows-style paths (`\`) may behave differently — recommend Unix-style ZIPs

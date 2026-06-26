# Project Submission AI Analyzer

A FastAPI service that takes a student's project ZIP + metadata, figures out which
skills (from a fixed catalog) the code actually demonstrates, generates mentor-ready
viva questions per skill, and compares the stated outcomes against real code evidence.

## Architecture

```
ZIP + metadata + skill catalog
        ↓
\[1] Safe ZIP Extractor (deterministic, guardrails)
        ↓
\[2] Skill Extractor Agent  ──uses──> RAG over skill\_catalog.json (OpenAI embeddings)
        ↓
\[3] Question Generator Agent (×2 per suggested skill) ──uses──> WebSearchTool
        ↓
\[4] Comparator Agent — outcomes vs code evidence
        ↓
\[5] Report compiler (deterministic) → final JSON
```

All LLM steps run through an **Orchestrator + Evaluator** (`orchestrator.py`):
after each agent call, the output is validated structurally (non-empty, correct
ranges, required fields present); a failing step is retried (up to 2x) before the
whole request fails with a clear error — so a bad agent call can't silently
corrupt the final report.

Built on the **OpenAI Agents SDK** (`agents` package), not raw chat completions —
each pipeline stage is a separate `Agent` with its own instructions, tools, and a
strict Pydantic `output\_type` so output is always structured.

### Why Streamlit isn't the API

The assignment requires a real `POST /analyze-submission` REST endpoint — Streamlit
apps don't expose that. So **FastAPI (`main.py`) is the actual graded API**, and
`streamlit\_app.py` is just a demo front-end that calls it over HTTP. Use it for your
demo video; the API itself works fine with curl/Postman/anything.

## Folder structure

```
project\_evaluator/
├── main.py                  # FastAPI app — POST /analyze-submission
├── orchestrator.py          # Orchestrator + Evaluator (retry logic)
├── schemas.py               # Pydantic models matching the required JSON shape
├── skill\_catalog.json       # Provided skill catalog (50 IT skills)
├── streamlit\_app.py         # Demo UI — calls the FastAPI endpoint
├── pipeline\_agents/
│   ├── skill\_agent.py       # RAG-grounded skill suggestion agent
│   ├── question\_agent.py    # Per-skill interview question generator (+ web search)
│   └── comparator\_agent.py  # Outcomes vs code evidence agent
├── rag/
│   └── catalog\_index.py     # Embedding-based retrieval over skill\_catalog.json
├── utils/
│   └── safe\_zip.py          # Safe ZIP extraction (path traversal, size limits, etc.)
├── tests/
│   └── test\_basic.py        # Unit tests (path traversal, empty zip, schema bounds)
├── sample\_test\_submission.zip  # Demo ZIP (small FastAPI CRUD app)
├── requirements.txt
├── pytest.ini
└── .env.example
```

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\\Scripts\\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env and set your real OPENAI\_API\_KEY
```

### Environment variables (`.env`)

|Variable|Default|Purpose|
|-|-|-|
|`OPENAI\_API\_KEY`|—|**required**, your OpenAI key|
|`OPENAI\_MODEL`|`gpt-4o-mini`|model used by all agents|
|`QUESTIONS\_PER\_SKILL\_DEFAULT`|`2`|used if the request doesn't override it|
|`MAX\_FILES\_ANALYZED`|`20`|cap on files sent to the LLM, to avoid context blowup|
|`MAX\_FILE\_SIZE\_BYTES`|`200000`|per-file size cap during extraction|
|`MAX\_ZIP\_SIZE\_BYTES`|`20000000`|total upload size cap (20 MB)|

## Running

```bash
uvicorn main:app --reload --port 8000
```

Health check: `GET http://localhost:8000/health`
Interactive docs: `http://localhost:8000/docs`

### Demo UI (optional)

```bash
streamlit run streamlit\_app.py
```

## Running tests

```bash
pytest tests/ -v
```

These cover path-traversal rejection, blocked-directory skipping, empty-zip
handling, and schema bounds — no API key needed since these tests only exercise
the deterministic extraction layer.

## Example API call

```bash
curl -X POST http://localhost:8000/analyze-submission \\
  -F "project\_title=Inventory Management API" \\
  -F "project\_description=A FastAPI service for managing inventory with JWT auth and Docker deployment." \\
  -F "project\_outcomes=1. Build a REST API for inventory management
2. Implement user authentication and secure API access
3. Deploy the application using Docker
4. Apply database design and normalization principles" \\
  -F "questions\_per\_skill=2" \\
  -F "zip\_file=@sample\_test\_submission.zip"
```

Response shape matches the spec exactly: `project\_title`, `suggested\_skills\[]`
(with `confidence` + `rationale`), `evaluation\_report.skills\[]` (questions per
skill, each tagged `conceptual` or `codebase\_specific`), `evaluation\_report.summary`
(outcome-by-outcome status + evidence + gap, overall alignment, narrative,
strengths, gaps), `evaluation\_report.metadata`, and `processing\_time\_ms`.

## Error handling

|Condition|HTTP status|
|-|-|
|Not a valid ZIP|400|
|Path traversal / unsafe ZIP contents|400|
|Empty project (no analyzable files)|422|
|Missing required fields|400|
|ZIP exceeds size limit|413|
|LLM/agent pipeline fails after retries|502|
|Missing `OPENAI\_API\_KEY`|500|

## Notes / design decisions

* **RAG grounding for skills**: the skill agent is only shown the catalog skills
the embedding index retrieved as relevant for the given code, and the
orchestrator additionally re-validates every suggested `skill\_id`/`skill\_name`
against the real catalog after the LLM responds — so a hallucinated skill can
never reach the final report, even if the model misbehaves.
* **Safe extraction**: blocks `../` traversal and absolute paths, skips
`node\_modules`/`.git`/`venv`/etc., enforces per-file and total size limits, and
caps the number of files actually sent to the LLM (largest relevant files first)
to avoid context overflow on big repos.
* **Questions per skill**: split roughly evenly between `conceptual` (web-search
grounded, current interview practice) and `codebase\_specific` (must cite a real
file/symbol from the extracted code — the evaluator rejects a batch that's
missing either type).


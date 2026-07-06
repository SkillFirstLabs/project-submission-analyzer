# Implementation Plan — Project Submission AI Analyzer with Proctored Live Viva

## 0. Read of the Brief (what's actually being asked)

Two pipelines that share one session lifecycle:

1. **Submission Analysis** (stateless, single request/response): ZIP → parse → skill suggestion → question generation → outcome-vs-evidence evaluation.
2. **Live Viva Proctoring** (stateful, streaming events): identity check → live event ingestion → integrity scoring.

They merge into one JSON at the end. The proctoring module is explicitly **event-based, not video-based** — this drives a lot of the architecture (no video storage, no CV pipeline server-side, just a scoring engine over a timestamped event stream).

Total build surface: 1 FastAPI app, ~3 route groups, 1 ZIP-safety layer, 1 LLM integration layer, 1 in-memory session store, 1 scoring engine, Pydantic schemas throughout, tests, README, demo video.

---

## 1. Tech Stack Decisions

| Concern | Choice | Why |
|---|---|---|
| Framework | FastAPI + Uvicorn | Required by brief |
| Language | Python 3.11+ | Required |
| LLM | Your own key — Anthropic (Claude) or OpenAI, via a thin adapter | Brief says "your own AI key"; keep it swappable |
| Validation | Pydantic v2 | Native to FastAPI, enforces the output schema in §6 of the brief |
| ZIP handling | `zipfile` + `pathlib` with manual path-traversal guards | Stdlib only, no DB needed |
| Session store | In-memory dict keyed by `session_id`, with a `threading.Lock` (or `asyncio.Lock`) | Brief explicitly forbids a DB; sessions are short-lived |
| Config | `pydantic-settings` + `.env` / `.env.example` | Keeps thresholds configurable, not hardcoded (explicit requirement) |
| Testing | `pytest` + `httpx.AsyncClient` (FastAPI TestClient) | Standard, fast |
| Client demo harness | Plain HTML + JS (getUserMedia + face-api.js or MediaPipe FaceMesh) | Only needed to *produce* the event stream for your demo video — not a deliverable per se, but you need something posting events |

---

## 2. Project Structure

```
project-submission-analyzer/
├── app/
│   ├── main.py                     # FastAPI app, routers mounted
│   ├── config.py                   # Settings via pydantic-settings
│   ├── schemas/
│   │   ├── analysis.py             # Request/response models for /analyze-submission
│   │   ├── viva.py                 # Event schema, session models
│   │   └── common.py               # Shared enums (Severity, RiskLevel, etc.)
│   ├── routers/
│   │   ├── analyze.py              # POST /analyze-submission
│   │   └── viva.py                 # /viva-session/start|event|end
│   ├── services/
│   │   ├── zip_extractor.py        # Safe extraction, file tree, dependency parse
│   │   ├── code_analyzer.py        # Snippet extraction, language/framework detection
│   │   ├── skill_suggester.py      # LLM call #1 — catalog-constrained skill matching
│   │   ├── question_generator.py   # LLM call #2 — per-skill questions
│   │   ├── outcome_evaluator.py    # LLM call #3 — outcomes vs evidence
│   │   ├── llm_client.py           # Thin wrapper around your chosen LLM API
│   │   └── proctoring_engine.py    # Event ingestion, scoring, flag thresholds
│   ├── store/
│   │   └── session_store.py        # In-memory session registry (thread/async-safe)
│   ├── data/
│   │   └── skill_catalog.json      # Provided catalog, loaded at startup
│   └── utils/
│       ├── security.py             # Path-traversal / zip-bomb guards
│       └── errors.py               # Custom exception → HTTP mapping
├── tests/
│   ├── test_zip_safety.py
│   ├── test_analyze_endpoint.py
│   ├── test_viva_events.py
│   └── test_schemas.py
├── client-demo/
│   └── index.html                  # Minimal getUserMedia + face-landmark demo page
├── sample_submission.zip           # Your own 5–15 file test project
├── .env.example
├── requirements.txt
├── README.md
└── NOTES.md                        # ½-page privacy write-up
```

---

## 3. Data Model Design (do this before writing routes)

Get Pydantic models locked first — everything else is built to satisfy them.

- `Skill`, `SuggestedSkill` (skill_id, skill_name, confidence, rationale)
- `Question` (skill_name, type: `conceptual`|`codebase_specific`, text, referenced_file — required when codebase_specific)
- `OutcomeStatus` enum: `met | partial | not_met | not_verifiable`
- `OutcomeEvaluation` (outcome_text, status, evidence[], gap)
- `EvaluationSummary` (overall_alignment, alignment_score, narrative, outcome_evaluation[], strengths[], gaps[])
- `EvaluationReport` (skills[], summary)
- `ProctoringEvent` (session_id, event_type enum, timestamp, duration_ms?, confidence?)
- `Flag` (type, timestamp, severity, duration_ms?)
- `ProctoringReport` (session_id, id_check, integrity_score, risk_level, flag_summary{}, flags[], narrative)
- `AnalyzeSubmissionResponse` — the full combined §6 payload, `metadata`, `processing_time_ms`

Doing this first means the LLM prompts can be written to directly target these shapes (ask the LLM to return JSON matching the schema, validate with Pydantic, retry once on failure).

---

## 4. Build Phases (sequential, each independently testable)

### Phase 1 — Skeleton & Config (0.5 day)
- FastAPI app boots, health check route.
- `.env.example` with `LLM_API_KEY`, `LLM_MODEL`, threshold vars (`GAZE_OFF_LOW_SEC`, `GAZE_OFF_MED_SEC`, `FACE_MISSING_SEC`, etc.).
- Load skill catalog JSON at startup into app state.
- **Exit criteria:** `uvicorn app.main:app` runs, `/health` returns 200, catalog loaded and logged.

### Phase 2 — Safe ZIP Extraction & Code Analysis (1 day)
- `zip_extractor.py`:
  - Reject if uncompressed size exceeds a configurable cap (zip-bomb guard).
  - Reject any entry whose resolved path escapes the extraction dir (`..`, absolute paths, symlink tricks) — **this is the flag-worthy path-traversal test** mentioned in deliverables.
  - Extract to a temp dir (`tempfile.TemporaryDirectory`), auto-cleaned after processing.
  - Build a file tree (path, size, extension).
  - Parse dependency files if present: `requirements.txt`, `package.json`, `pyproject.toml`.
- `code_analyzer.py`:
  - Pick representative snippets: entrypoints (`main.py`, `app.py`, `index.js`), largest files, files matching common framework patterns (routers, models, migrations).
  - Cap total tokens sent to the LLM (truncate per-file, prioritize breadth over depth).
- **Exit criteria:** given any ZIP, you get back `{file_tree, dependencies, snippets, language_guess}` and malicious ZIPs are rejected with a clear 4xx.

### Phase 3 — Skill Suggestion (0.5–1 day)
- `skill_suggester.py`: single LLM call.
  - Prompt includes: catalog (skill_id + name only, nothing else — LLM must not invent IDs), file tree summary, dependency list, code snippets.
  - Instruct: "Only return skill_ids present in this catalog. If none genuinely apply, return an empty list."
  - Parse response into `SuggestedSkill[]`, validate every `skill_id` against the catalog server-side (defense in depth — don't trust the LLM to obey instructions) and drop/flag any hallucinated ID.
- **Exit criteria:** for a known FastAPI+Postgres test ZIP, correct skills come back with plausible confidence + rationale referencing real files.

### Phase 4 — Question Generation (0.5 day)
- `question_generator.py`: per suggested skill, request `questions_per_skill` questions, enforcing at least one `conceptual` and one `codebase_specific`.
- For `codebase_specific`, require the LLM to name an actual file/symbol from the snippets you supplied — validate post-hoc with a simple substring check against the file tree; regenerate once if it fails.
- **Exit criteria:** every codebase_specific question cites a real path in the extracted project.

### Phase 5 — Outcome Evaluation / Summary (1 day)
- `outcome_evaluator.py`:
  - Split `project_outcomes` on newlines / numbered bullets (`re.split` on `\n|^\d+[\.\)]`).
  - For each outcome, ask the LLM to find supporting evidence *only* from the supplied snippets/file tree, and classify `met|partial|not_met|not_verifiable`.
  - Aggregate into `overall_alignment` + `alignment_score` (can be LLM-produced or a simple weighted average you compute from per-outcome statuses — computing it yourself is more defensible/deterministic).
  - Generate the 2–4 sentence narrative last, after you have the structured data, so it stays grounded.
- **Exit criteria:** `evaluation_report` matches schema exactly; evidence strings reference real filenames.

At this point `/analyze-submission` is fully functional end-to-end. **Write its tests now**, before moving to proctoring, so you have a stable baseline.

### Phase 6 — Proctoring Engine core (1 day)
- `session_store.py`: `{session_id: {status, events[], id_check, started_at, last_event_at}}`.
- `POST /viva-session/start`:
  - Requires the `analyze-submission` result reference (or its session-linkage id).
  - Creates session, expects `interview_started` as the first event, then blocks "questioning" state until `id_verified`/`id_failed` is received (per brief: identity check must resolve before questioning begins — enforce this as a state machine, not just a convention).
- `POST /viva-session/event`:
  - Validates against `ProctoringEvent` schema.
  - Appends to session event log, updates `last_event_at`.
  - Runs the event through `proctoring_engine.score_event()` which applies **configurable** severity thresholds (from `.env`/settings, not hardcoded ints) to produce a `Flag` for threshold-crossing events (`gaze_off_screen`, `face_not_detected`, etc.); binary events (`tab_switched`, `paste_attempted`, `screenshot_detected`, `fullscreen_exited`, `multiple_faces_detected`) flag immediately with a severity based on frequency/count within the session.
- `POST /viva-session/end`:
  - Marks session closed.
  - Computes `integrity_score` (start at 1.0, subtract weighted penalties per flag severity — weights configurable) and `risk_level` bucketed from the score.
  - Builds `flag_summary` (counts by type) and `flags[]` (full list).
  - Generates a short mentor-facing narrative (LLM call or a template-based summary — template is safer/cheaper here since the data is already structured).
- **Dead-session handling:** a background check (or a check performed lazily on `/end`) compares `last_event_at` against `now`; if the gap exceeds a configurable "connection lost" threshold, inject a synthetic `connection_lost` flag rather than silently returning a clean report. This directly satisfies the brief's explicit rule about dropped connections not being treated as clean.
- **Exit criteria:** simulate a full event sequence via test client and confirm accumulated flags → correct score/risk bucket; simulate silence and confirm the connection-lost flag appears.

### Phase 7 — Consent + Session Linkage (0.5 day)
- `POST /viva-session/start` requires a `consent_acknowledged: true` field in the request; reject with 400 if missing — this is the "one-time consent notice" requirement, enforced server-side even though the actual UI notice lives client-side.
- Link the viva session back to the `analyze-submission` output (e.g. pass the earlier response's questions/skills back in, or cache the analysis result server-side by an id returned from `/analyze-submission` — since there's no DB, an in-memory cache with a TTL is fine here too).

### Phase 8 — Merge & Final Response Assembly (0.5 day)
- On `/viva-session/end`, return the full combined §6 JSON: `suggested_skills`, `evaluation_report`, `proctoring_report`, `metadata` (files_analyzed, extraction_time_ms, model_tokens_used), `processing_time_ms`.
- Wire `metadata` collection through every phase (timers around extraction and LLM calls, token counts from LLM responses).

### Phase 9 — Error Handling Pass (0.5 day)
- Central exception handlers mapping to clear HTTP codes:
  - Bad/corrupt ZIP → 400
  - Path traversal / zip bomb attempt → 400 with explicit reason
  - Empty project outcomes / missing required fields → 422 (FastAPI handles most via Pydantic)
  - Invalid catalog on startup → fail fast at boot
  - LLM timeout/failure → 502, with one retry already attempted internally
  - Event posted to unknown/closed session → 404/409
  - Malformed proctoring event → 422

### Phase 10 — Client Demo Harness (0.5–1 day)
- A minimal static page (`client-demo/index.html`) using `getUserMedia` + `face-api.js` (or MediaPipe FaceMesh) purely to *generate* real events for your demo:
  - Shows the consent notice, gates camera start on acknowledgment.
  - Runs a lightweight gaze/face-presence check client-side.
  - Wires `document.visibilitychange`, `fullscreenchange`, `paste`, and a best-effort screenshot detection (e.g. `Ctrl+PrintScreen` keydown / blur heuristics — full screenshot detection isn't reliably possible in-browser, note this honestly in your write-up).
  - POSTs events to `/viva-session/event` as they occur.
- This isn't a scored deliverable item by name, but you cannot record the required demo video (which needs a real triggered flag) without it.

### Phase 11 — Tests (0.5–1 day)
Minimum, mapped directly to the brief's suggestions:
1. Path-traversal ZIP rejected (craft a zip with `../../etc/passwd` entry).
2. Oversized/zip-bomb rejected.
3. Proctoring event schema validation (missing field, bad enum value → 422).
4. Full `/analyze-submission` happy path → response validates against `AnalyzeSubmissionResponse`.
5. Session lifecycle: event before `id_verified` is rejected or queued correctly per your state machine.
6. Silence → connection-lost flag appears.
7. Severity thresholds respect `.env` overrides (monkeypatch settings, confirm behavior changes).

### Phase 12 — README, NOTES, Sample ZIP, Packaging (0.5 day)
- README: setup steps, env vars table, folder structure, test command, one full `curl`/`httpie` example for `/analyze-submission`, one example flow (start → event → event → end) for viva, demo video link placeholder.
- NOTES.md: ½-page on the privacy approach — emphasize client-side-only landmark extraction, event-only transport, no frame storage, consent gating, and the honest limitation around screenshot detection.
- Build your own 5–15 file sample project (e.g. small FastAPI CRUD app) and zip it — this doubles as your test fixture and your demo submission.

### Phase 13 — Demo Video & Submission (0.5 day)
- Record per the brief's required shot list: boot server → `/analyze-submission` call with real ZIP → live viva run with at least one deliberately triggered flag (switch tabs or look away) → show the final merged JSON → 1–2 min code walkthrough + one design decision explained (e.g. why events-not-video, or why thresholds are configurable).
- Branch per naming convention, commit (never commit `.env`), push, open for review.

---

## 5. Suggested Timeline (solo dev, focused effort)

| Day | Work |
|---|---|
| 1 | Phase 1–2 (skeleton, ZIP safety/parsing) |
| 2 | Phase 3–4 (skills, questions) |
| 3 | Phase 5 (outcome evaluation) + tests for analysis pipeline |
| 4 | Phase 6–7 (proctoring engine, consent, session linkage) |
| 5 | Phase 8–9 (merge, error handling) + Phase 11 tests |
| 6 | Phase 10 (client demo harness) |
| 7 | Phase 12–13 (docs, sample zip, recording, submission) |

Compress to 3–4 days if you skip the optional unit tests and keep the client demo harness minimal (a hand-triggered fetch() button instead of a real face-landmark model is acceptable for demo purposes — just be transparent about it in NOTES.md).

---

## 6. Risk Areas Worth Front-Loading

- **LLM output reliability**: never trust raw LLM JSON. Always parse → validate with Pydantic → on failure, do one repair retry with the validation error fed back into the prompt → on second failure, degrade gracefully (e.g. `not_verifiable` outcomes, empty skill list) rather than 500ing.
- **Hallucinated file references**: cross-check every "codebase_specific" claim against the real file tree programmatically; don't rely on prompting alone.
- **State machine correctness for viva sessions**: this is the part reviewers will actually probe in the demo (triggering a flag live) — get `start → id_check → events → end` airtight before polishing anything else.
- **Configurability**: every threshold (severity cutoffs, connection-lost timeout, integrity score weights) must load from settings, not be a magic number in `proctoring_engine.py` — the brief calls this out explicitly and it's an easy point to lose.

---

## 7. Immediate Next Step

Start with Phase 1 + the Pydantic schemas in Section 3 — everything downstream (prompts, tests, routes) is easier to write correctly once the response shape is nailed down and the server boots cleanly.

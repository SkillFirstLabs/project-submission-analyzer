# Project Submission AI Analyzer (with Proctored Live Viva)

A FastAPI service that takes a student's project ZIP through to a mentor-ready
evaluation: it analyzes the codebase, suggests skills from a fixed catalog,
generates grounded interview questions, runs a proctored live viva, and
returns one combined JSON report.

A minimal web UI (`static/`) is included so you can run the whole flow —
upload → analysis → consent → live viva with webcam → final report — from
a browser, which also makes it easy to record the required demo video.

## 1. Setup

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# then edit .env and set ANTHROPIC_API_KEY
```

Environment variables are documented inline in `.env.example` — API key,
model name, ZIP size limits, and every proctoring threshold (all
configurable, none hardcoded, per the brief).

## 2. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Then open **http://localhost:8000** in your browser (Chrome recommended,
for webcam + face detection support).

## 3. Folder structure

```
app/
  main.py            # FastAPI routes
  config.py          # env-driven settings (thresholds, limits, model name)
  schemas.py          # Pydantic models for every request/response
  zip_analyzer.py     # safe ZIP extraction + evidence building
  skill_engine.py      # LLM calls: skill suggestion, questions, outcome eval
  llm_client.py        # thin Anthropic API wrapper (JSON-only responses)
  proctoring.py        # session lifecycle, event scoring, watchdog
static/
  index.html, style.css, app.js   # the UI described above
data/
  skill_catalog.json   # sample skill catalog
tests/
  test_zip_safety.py    # path-traversal / empty-zip rejection
  test_proctoring.py    # event schema + integrity scoring
sample_test.zip         # a small demo FastAPI+SQLAlchemy todo app, zipped
```

## 4. Run tests

```bash
pytest tests/ -v
```

## 5. Example API call — `/analyze-submission`

```bash
curl -X POST http://localhost:8000/analyze-submission \
  -F "project_title=Todo API" \
  -F "project_description=A small FastAPI todo list service" \
  -F "project_outcomes=Build a REST API for managing todos
Persist todos in a database
Support marking todos as complete" \
  -F "questions_per_skill=2" \
  -F "zip_file=@sample_test.zip"
```

This returns `submission_id`, `suggested_skills`, `evaluation_report`
(questions + outcome summary), and `metadata`.

## 6. Example flow — `/viva-session/*`

```bash
# 1. Start a session (requires consent_acknowledged = true)
curl -X POST http://localhost:8000/viva-session/start \
  -H "Content-Type: application/json" \
  -d '{"submission_id": "sub-xxxx", "consent_acknowledged": true}'

# 2. Post integrity events as they happen (repeat as needed)
curl -X POST http://localhost:8000/viva-session/event \
  -H "Content-Type: application/json" \
  -d '{"session_id": "sess-xxxx", "event_type": "gaze_off_screen",
       "timestamp": "2026-07-05T10:12:03Z", "duration_ms": 4200, "confidence": 0.81}'

# 3. End the session -> get the combined evaluation + proctoring report
curl -X POST http://localhost:8000/viva-session/end -F "session_id=sess-xxxx"
```

In the browser UI, steps 1–3 happen automatically: webcam + tab-visibility +
fullscreen + paste listeners fire events for you as you click through the
questions, and clicking **"End Session"** produces the final combined JSON
shown in `/viva-session/end`'s response.

## 7. Design notes

**Privacy approach for proctoring.** No frame or audio ever leaves the
browser. Face detection runs client-side via `face-api.js`'s tiny face
detector loaded from a CDN; the app only derives a face-count and a rough
on-screen/off-screen position from that, and posts short, timestamped event
objects (`gaze_off_screen`, `face_not_detected`, etc.) matching the schema in
the brief. Tab-switch and fullscreen-exit signals come from standard browser
APIs (Page Visibility, Fullscreen), not from any video analysis at all. If
the client stops sending events (camera denied, connection dropped), a
server-side watchdog notices the gap and injects a `connection_lost` flag
itself, so a silent client never reads as a clean session.

**Known limitations (documented, not hidden):**
- The in-browser "gaze" signal is a simple face-bounding-box-position proxy,
  not true eye-gaze tracking — good enough to demonstrate the pipeline, not
  a research-grade gaze estimator.
- `screenshot_detected` is best-effort only (PrintScreen keydown); most
  screenshot tools are not reliably detectable from a browser sandbox, and
  this is called out in the code comment where it's implemented.
- The skill catalog is a single JSON file, per spec — no admin UI to edit it.

## 8. Submission checklist (for the internship task)

- [ ] Push to your branch: `<college-id>-<full-name-in-lowercase-with-hyphens>`
- [ ] Do **not** commit `.env` — only `.env.example`
- [ ] Record the 5–10 min demo video: server start → `/analyze-submission`
      call → live viva with at least one deliberately triggered flag (e.g.
      switch tabs mid-session) → final combined JSON → brief code walkthrough
- [ ] Include your own test ZIP (5–15 files) — `sample_test.zip` here is a
      starting point; swap in your own project if you'd like

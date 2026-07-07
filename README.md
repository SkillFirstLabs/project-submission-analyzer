# AIvaluate: Project Submission & Proctoring Engine

This system uses AI to analyze student codebase submissions, generate viva questions, and conduct a live proctored interview. 
The application now supports **Role-Based Access Control (RBAC)** separating Student and Mentor flows.

## Roles
- **Student**: Can upload project ZIPs, join their viva session, and see generic success metrics.
- **Mentor**: Can view all submissions, start live viva sessions with real-time SSE telemetry, and export PDF/JSON evaluation reports.

## Local Setup

### 1. Database & Backend
```bash
cd backend
pip install -r requirements.txt
cp .env.example .env
# Make sure to set your GEMINI_API_KEY in .env

# Start the server (SQLite tables will be auto-created on startup)
python app/main.py
```

### 2. Testing Accounts
You can create your own accounts via the `/auth/register` API or the frontend registration page.
- Choose "student" role to test project uploads.
- Choose "mentor" role to test the dashboard, SSE live proctoring, and PDF exports.

### 3. Frontend
```bash
cd frontend
npm install
npm run dev
```

---

## Environment Variables
The backend configuration is managed using environment variables. Below is the list of supported settings:

| Variable | Description |
|---|---|
| `DATABASE_URL` | Connection URL for SQLite database. Defaults to `sqlite+aiosqlite:///./app.db`. |
| `JWT_SECRET` | Secret key for signing and verifying JWT tokens. Defaults to `supersecretkey_change_me_in_prod`. |
| `GEMINI_API_KEY` | API key to access Google's Gemini models for evaluation. |
| `GROQ_API_KEY` | (Optional) Fallback/alternative API key for llama-3 models via Groq. |
| `PORT` | Port for the backend application server. Defaults to `8000`. |
| `HOST` | Binds server to specified host network interface. Defaults to `0.0.0.0`. |
| `GAZE_OFF_SCREEN_THRESHOLD_SEC` | Seconds student gaze can be off-screen before generating a flag. Defaults to `3.0`. |
| `FACE_NOT_DETECTED_THRESHOLD_SEC` | Seconds the face can be undetected before generating a flag. Defaults to `5.0`. |
| `CONNECTION_LOST_TIMEOUT_SEC` | Timeout before inactive connection triggers a connection lost flag. Defaults to `15.0`. |
| `GAZE_OFF_SCREEN_PENALTY` | Score penalty deducted for gaze off-screen flags. Defaults to `0.05`. |
| `MULTIPLE_FACES_PENALTY` | Score penalty deducted for multiple face flags. Defaults to `0.2`. |
| `FACE_NOT_DETECTED_PENALTY` | Score penalty deducted for face not detected flags. Defaults to `0.1`. |
| `TAB_SWITCHED_PENALTY` | Score penalty deducted for tab switching flags. Defaults to `0.1`. |
| `FULLSCREEN_EXITED_PENALTY` | Score penalty deducted for exiting fullscreen mode. Defaults to `0.15`. |
| `PASTE_ATTEMPTED_PENALTY` | Score penalty deducted for copying/pasting. Defaults to `0.1`. |
| `SCREENSHOT_DETECTED_PENALTY` | Score penalty deducted for screenshot attempts. Defaults to `0.2`. |
| `CONNECTION_LOST_PENALTY` | Score penalty deducted for connection lost. Defaults to `0.3`. |

---

## Repository Structure
```
AIvaluate/
├── backend/                  # FastAPI backend application
│   ├── app/                  # Main backend source files
│   │   ├── db/               # Database models and async SQLAlchemy connection
│   │   ├── routers/          # API routers (auth, analyze, viva, mentor, dashboard, export)
│   │   ├── schemas/          # Pydantic schemas for data validation
│   │   └── services/         # Core business logic (LLM integrations, extraction, proctoring engine)
│   └── tests/                # Automated pytest suite (unit, RBAC, and backend tests)
└── frontend/                 # Vite + React frontend web application
    ├── src/                  # React source files (components, telemetry emitters, view routing)
    └── public/               # Public assets and icons
```
* **Backend**: Powered by FastAPI, it handles secure API endpoints, JWT-based authentication, async SQLite management via SQLAlchemy, and proctoring evaluation metrics.
* **Frontend**: A single-page React app styled with vanilla CSS, implementing real-time webcam rendering, MediaPipe FaceMesh face mesh tracking, and telemetry event streaming.

---

## Running Tests
To execute the backend automated test suite, navigate to the `backend` directory and run `pytest`:
```bash
cd backend
pytest tests/ -v
```

---

## Example API Calls

### 1. Analyze Submission (`POST /analyze-submission`)
Uploads a code repository ZIP and extracts core features for viva questions:
```bash
curl -X POST "http://localhost:8000/analyze-submission" \
  -H "Authorization: Bearer <STUDENT_JWT_TOKEN>" \
  -H "Content-Type: multipart/form-data" \
  -F "project_title=AI powered Proctoring Web App" \
  -F "project_description=Full stack app utilizing MediaPipe on React and FastAPI." \
  -F "project_outcomes=Uses MediaPipe face tracking to flag tab switching and off-screen gazes." \
  -F "zip_file=@/path/to/project_code.zip" \
  -F "questions_per_skill=2"
```

### 2. End-to-End Proctoring Session Flow

#### Step A: Start the Session
Requires explicit student consent acknowledgment:
```bash
curl -X POST "http://localhost:8000/viva-session/start" \
  -H "Authorization: Bearer <STUDENT_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SUBMISSION_ID_HERE",
    "consent_acknowledged": true
  }'
```

#### Step B: Send Identity Verification Event
Resolves the pending identity verification check:
```bash
curl -X POST "http://localhost:8000/viva-session/event" \
  -H "Authorization: Bearer <STUDENT_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SUBMISSION_ID_HERE",
    "event_type": "id_verified",
    "timestamp": "2026-07-06T14:10:00Z",
    "duration_ms": 0.0,
    "confidence": 1.0
  }'
```

#### Step C: Send Telemetry Proctoring Event
Flags a proctoring issue (e.g. switching tabs):
```bash
curl -X POST "http://localhost:8000/viva-session/event" \
  -H "Authorization: Bearer <STUDENT_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SUBMISSION_ID_HERE",
    "event_type": "tab_switched",
    "timestamp": "2026-07-06T14:10:05Z",
    "duration_ms": 0.0,
    "confidence": 1.0
  }'
```

#### Step D: End the Session
Completes questioning and computes the final integrity report:
```bash
curl -X POST "http://localhost:8000/viva-session/end" \
  -H "Authorization: Bearer <STUDENT_JWT_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "SUBMISSION_ID_HERE",
    "questions": [{"text": "What is FastAPI?", "skill_name": "FastAPI", "type": "conceptual"}],
    "answers": {"0": "FastAPI is a modern web framework."}
  }'
```

---

## Known Limitations
* **Simulated Identity Verification**: The identity check implemented in the frontend is currently a placeholder that only checks for webcam access, rather than performing actual biometric student verification. A production-ready version should capture a camera frame client-side and compare it against a stored enrollment photo before firing `id_verified`.

---

## Demo Video
Demo video: https://www.youtube.com/watch?v=44Vxx9FxvWI

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

import time
from typing import Dict, Any, Optional
import threading

class SessionStore:
    def __init__(self):
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def create_session(self, session_id: str, analysis_data: Dict[str, Any]) -> Dict[str, Any]:
        with self._lock:
            now = time.time()
            session = {
                "session_id": session_id,
                "project_title": analysis_data.get("project_title", "Unknown Project"),
                "suggested_skills": analysis_data.get("suggested_skills", []),
                "evaluation_report": analysis_data.get("evaluation_report", {}),
                "id_check": "pending",
                "started_at": now,
                "last_event_at": now,
                "is_ended": False,
                "events": [],
                "flags": [],
                "metadata": analysis_data.get("metadata", {})
            }
            self._sessions[session_id] = session
            return session

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._sessions.get(session_id)

    def update_session(self, session_id: str, updates: Dict[str, Any]):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(updates)
                self._sessions[session_id]["last_event_at"] = time.time()

    def add_event(self, session_id: str, event: Dict[str, Any]):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["events"].append(event)
                self._sessions[session_id]["last_event_at"] = time.time()

    def add_flag(self, session_id: str, flag: Dict[str, Any]):
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id]["flags"].append(flag)

    def list_active_sessions(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return {k: v for k, v in self._sessions.items() if not v["is_ended"]}

session_store = SessionStore()

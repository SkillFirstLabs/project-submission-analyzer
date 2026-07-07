import uuid
from datetime import datetime, timezone

from app.config import (
    EVENT_PENALTIES,
    LOW_RISK_THRESHOLD,
    MEDIUM_RISK_THRESHOLD
)


sessions = {}


ALLOWED_EVENT_TYPES = {
    "face_not_detected",
    "multiple_faces_detected",
    "gaze_off_screen",
    "tab_switched",
    "fullscreen_exited",
    "paste_attempted"
}


def create_viva_session():
    session_id = str(uuid.uuid4())

    sessions[session_id] = {
        "session_id": session_id,
        "id_check": "pending",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "ended_at": None,
        "status": "active",
        "events": []
    }

    return sessions[session_id]


def add_proctoring_event(
    session_id,
    event_type,
    duration_ms=None,
    confidence=None
):
    if session_id not in sessions:
        return None, "Session not found"

    session = sessions[session_id]

    if session["status"] != "active":
        return None, "Session is not active"

    if event_type not in ALLOWED_EVENT_TYPES:
        return None, "Invalid event type"

    event = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "duration_ms": duration_ms,
        "confidence": confidence
    }

    session["events"].append(event)

    return event, None


def calculate_proctoring_report(session):
    events = session["events"]

    integrity_score = 1.0
    flag_summary = {}

    for event in events:
        event_type = event["event_type"]

        flag_summary[event_type] = (
            flag_summary.get(event_type, 0) + 1
        )

        penalty = EVENT_PENALTIES.get(
            event_type,
            0
        )

        integrity_score -= penalty

    integrity_score = max(
        0.0,
        round(integrity_score, 2)
    )

    if integrity_score >= LOW_RISK_THRESHOLD:
        risk_level = "low"

    elif integrity_score >= MEDIUM_RISK_THRESHOLD:
        risk_level = "medium"

    else:
        risk_level = "high"

    return {
        "session_id": session["session_id"],
        "id_check": session["id_check"],
        "integrity_score": integrity_score,
        "risk_level": risk_level,
        "flag_summary": flag_summary,
        "flags": events
    }


def end_viva_session(session_id):
    if session_id not in sessions:
        return None, "Session not found"

    session = sessions[session_id]

    if session["status"] != "active":
        return None, "Session has already ended"

    session["status"] = "completed"

    session["ended_at"] = (
        datetime.now(timezone.utc).isoformat()
    )

    proctoring_report = calculate_proctoring_report(
        session
    )

    session["proctoring_report"] = proctoring_report

    return session, None
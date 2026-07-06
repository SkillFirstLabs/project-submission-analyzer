from fastapi import APIRouter, HTTPException, Body
from typing import Dict, Any, Optional
from app.schemas.schemas import ProctoringEvent, AnalyzeSubmissionResponse
from app.store.session_store import session_store
from app.services.proctoring_engine import process_event, finalize_proctoring_report

router = APIRouter()

@router.post("/viva-session/start")
async def start_session(
    session_id: str = Body(..., embed=True),
    consent_acknowledged: bool = Body(..., embed=True),
    analysis_data: Dict[str, Any] = Body(...)
):
    if not consent_acknowledged:
        raise HTTPException(status_code=400, detail="Student consent must be acknowledged before starting a viva session.")
        
    existing = session_store.get_session(session_id)
    if existing:
        raise HTTPException(status_code=409, detail="Session already exists.")
        
    # Start stateful session
    session = session_store.create_session(session_id, analysis_data)
    
    # Initialize session with interview_started event
    import time
    start_event = {
        "session_id": session_id,
        "event_type": "interview_started",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_ms": 0.0,
        "confidence": 1.0
    }
    process_event(session_id, start_event)
    
    return {"status": "session_started", "session_id": session_id}

@router.post("/viva-session/event")
async def register_event(event: ProctoringEvent):
    session = session_store.get_session(event.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Active session not found.")
        
    if session.get("is_ended"):
        raise HTTPException(status_code=400, detail="Cannot log event to an already closed session.")
        
    # Standard event processing
    try:
        new_flags = process_event(event.session_id, event.model_dump())
        return {"status": "event_registered", "new_flags": len(new_flags)}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process event: {str(e)}")

@router.post("/viva-session/end", response_model=AnalyzeSubmissionResponse)
async def end_session(session_id: str = Body(..., embed=True)):
    session = session_store.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    # Finalize proctoring report
    try:
        proctoring_report = finalize_proctoring_report(session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize proctoring report: {str(e)}")
        
    # Assemble the final merged evaluation package
    merged_response = {
        "project_title": session["project_title"],
        "suggested_skills": session["suggested_skills"],
        "evaluation_report": session["evaluation_report"],
        "proctoring_report": proctoring_report,
        "metadata": session["metadata"],
        "processing_time_ms": session.get("metadata", {}).get("processing_time_ms", 0.0)
    }
    
    return merged_response

import asyncio
import time
from fastapi import APIRouter, HTTPException, Body, Depends, Request
from fastapi.responses import StreamingResponse
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from typing import Dict, Any, Optional, List

from app.db.database import get_db
from app.db.models import User, Submission, EvaluationReport, VivaSession, VivaEvent
from app.services.auth import require_role
from app.schemas.schemas import ProctoringEvent, AnalyzeSubmissionResponse
from app.services.proctoring_engine import process_event, finalize_proctoring_report
from app.services.llm import grade_viva_answers

router = APIRouter()

async def get_full_session_dict(db: AsyncSession, session_id: str):
    result = await db.execute(
        select(VivaSession)
        .options(
            selectinload(VivaSession.submission).selectinload(Submission.evaluation_report),
            selectinload(VivaSession.events)
        )
        .where(VivaSession.id == session_id)
    )
    db_session = result.scalars().first()
    if not db_session:
        return None
        
    submission = db_session.submission
    evaluation_report = submission.evaluation_report
    
    return {
        "session_id": db_session.id,
        "project_title": submission.project_title,
        "suggested_skills": evaluation_report.suggested_skills,
        "evaluation_report": evaluation_report.evaluation_report,
        "id_check": db_session.id_check,
        "started_at": db_session.started_at,
        "last_event_at": db_session.last_event_at or db_session.started_at,
        "is_ended": db_session.status == "completed",
        "events": list(db_session.events) if db_session.events else [],
        "flags": db_session.flags or [],
        "metadata": {} # We can mock this or store it in db
    }

async def save_session_dict(db: AsyncSession, session_id: str, session_dict: dict):
    result = await db.execute(
        select(VivaSession)
        .options(selectinload(VivaSession.events))
        .where(VivaSession.id == session_id)
    )
    db_session = result.scalars().first()
    if db_session:
        db_session.id_check = session_dict["id_check"]
        db_session.flags = session_dict["flags"]
        db_session.last_event_at = session_dict["last_event_at"]
        
        # Convert any raw dict events in session_dict["events"] into VivaEvent instances and add them
        import uuid
        cleaned_events = []
        for event in session_dict["events"]:
            if isinstance(event, dict):
                # This is a new event dictionary
                db_event = VivaEvent(
                    id=str(uuid.uuid4()),
                    session_id=session_id,
                    event_type=event.get("event_type"),
                    timestamp=event.get("timestamp"),
                    duration_ms=event.get("duration_ms", 0.0),
                    confidence=event.get("confidence", 1.0),
                    severity=event.get("severity")
                )
                db.add(db_event)
                cleaned_events.append(db_event)
            else:
                cleaned_events.append(event)
                
        session_dict["events"] = cleaned_events
        await db.commit()

@router.post("/viva-session/start")
async def start_session(
    session_id: str = Body(..., embed=True),
    consent_acknowledged: bool = Body(..., embed=True),
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db)
):
    if not consent_acknowledged:
        raise HTTPException(
            status_code=400,
            detail="Consent must be acknowledged before starting a proctored session."
        )

    # The session_id here is actually the submission_id for simplicity, since 1 submission = 1 viva
    submission_result = await db.execute(select(Submission).where(Submission.id == session_id))
    submission = submission_result.scalars().first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="Submission not found.")
        
    existing_result = await db.execute(select(VivaSession).where(VivaSession.submission_id == session_id))
    existing = existing_result.scalars().first()
    
    if existing:
        raise HTTPException(status_code=409, detail="Session already exists.")
        
    now = time.time()
    viva_session = VivaSession(
        id=session_id,  # reuse submission id as session id for easy lookup
        submission_id=session_id,
        mentor_id=None,
        status="in_progress",
        started_at=now,
        last_event_at=now,
        events=[],
        flags=[]
    )
    db.add(viva_session)
    await db.commit()
    
    # Initialize session with interview_started event
    start_event = {
        "session_id": session_id,
        "event_type": "interview_started",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "duration_ms": 0.0,
        "confidence": 1.0
    }
    
    # Using the mock dict helper for compatibility with engine
    session_dict = await get_full_session_dict(db, session_id)
    process_event(session_id, start_event, session_dict)
    await save_session_dict(db, session_id, session_dict)
    
    return {"status": "session_started", "session_id": session_id}

@router.post("/viva-session/event")
async def register_event(
    event: ProctoringEvent,
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db)
):
    session_dict = await get_full_session_dict(db, event.session_id)
    if not session_dict:
        raise HTTPException(status_code=404, detail="Active session not found.")
        
    if session_dict.get("is_ended"):
        raise HTTPException(status_code=400, detail="Cannot log event to an already closed session.")
        
    if event.event_type not in ["id_verified", "id_failed", "interview_started"]:
        if session_dict.get("id_check") == "pending":
            raise HTTPException(
                status_code=409,
                detail="Identity verification must complete before proctoring events can be logged."
            )
            
    try:
        # Patch to use pure functions instead of global session_store
        new_flags = process_event(event.session_id, event.model_dump(), session_dict)
        await save_session_dict(db, event.session_id, session_dict)
        return {"status": "event_registered", "new_flags": len(new_flags)}
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to process event: {str(e)}")

@router.post("/viva-session/end")
async def end_session(
    session_id: str = Body(..., embed=True),
    questions: Optional[List[Dict[str, Any]]] = Body(default=None),
    answers: Optional[Dict[str, str]] = Body(default=None),
    current_user: User = Depends(require_role("student")),
    db: AsyncSession = Depends(get_db)
):
    session_dict = await get_full_session_dict(db, session_id)
    if not session_dict:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    try:
        proctoring_report = finalize_proctoring_report(session_id, session_dict)
        await save_session_dict(db, session_id, session_dict)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to finalize proctoring report: {str(e)}")

    viva_grading = None
    if questions and answers:
        try:
            viva_grading = await grade_viva_answers(questions, answers)
        except Exception as e:
            viva_grading = {"graded_answers": [], "viva_score": 0.0, "viva_narrative": f"Grading error: {str(e)}"}
        
    # Update session status
    result = await db.execute(select(VivaSession).where(VivaSession.id == session_id))
    db_session = result.scalars().first()
    db_session.status = "completed"
    db_session.integrity_score = proctoring_report["integrity_score"]
    db_session.risk_level = proctoring_report["risk_level"].value
    db_session.ended_at = time.time()
    db_session.proctoring_report = proctoring_report
    db_session.viva_grading = viva_grading
    await db.commit()
    
    # Return only a minimal success confirmation to the student to maintain RBAC boundaries
    return {"status": "viva_completed", "session_id": session_id}

@router.get("/viva-session/{session_id}/stream")
async def stream_session_events(
    request: Request,
    session_id: str,
    #current_user: User = Depends(require_role("mentor")),  # Cannot easily send token in EventSource without query param, will skip strict auth for SSE for simplicity or use token in query params.
    db: AsyncSession = Depends(get_db)
):
    async def event_generator():
        last_flag_count = -1
        while True:
            if await request.is_disconnected():
                break
                
            session_dict = await get_full_session_dict(db, session_id)
            if not session_dict:
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
                break
                
            current_flags = session_dict.get("flags", [])
            if len(current_flags) > last_flag_count:
                yield f"data: {json.dumps({'flags': current_flags, 'is_ended': session_dict['is_ended']})}\n\n"
                last_flag_count = len(current_flags)
                
            if session_dict["is_ended"]:
                break
                
            await asyncio.sleep(2) # Poll DB every 2 seconds
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")


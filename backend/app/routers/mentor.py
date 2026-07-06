from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Dict, Any

from app.db.database import get_db
from app.db.models import User, VivaSession, Submission
from app.services.auth import require_role
from app.routers.viva import get_full_session_dict

router = APIRouter(prefix="/mentor", tags=["mentor"])

@router.get("/sessions")
async def list_completed_sessions(
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns all completed viva sessions for mentor review.
    """
    result = await db.execute(
        select(VivaSession, Submission)
        .join(Submission, VivaSession.submission_id == Submission.id)
        .where(VivaSession.status == "completed")
        .order_by(VivaSession.ended_at.desc())
    )
    
    rows = result.all()
    
    sessions_list = []
    for viva, sub in rows:
        sessions_list.append({
            "session_id": viva.id,
            "project_title": sub.project_title,
            "integrity_score": viva.integrity_score,
            "risk_level": viva.risk_level,
            "ended_at": viva.ended_at
        })
        
    return sessions_list

@router.get("/sessions/{session_id}")
async def get_session_report(
    session_id: str,
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns the full detailed report for a specific session.
    """
    session_dict = await get_full_session_dict(db, session_id)
    if not session_dict:
        raise HTTPException(status_code=404, detail="Session not found.")
        
    result = await db.execute(select(VivaSession).where(VivaSession.id == session_id))
    db_session = result.scalars().first()
    
    merged_response = {
        "project_title": session_dict["project_title"],
        "suggested_skills": session_dict["suggested_skills"],
        "evaluation_report": session_dict["evaluation_report"],
        "proctoring_report": db_session.proctoring_report,
        "viva_grading": db_session.viva_grading,
        "metadata": session_dict["metadata"],
        "processing_time_ms": 0.0
    }
    
    return merged_response

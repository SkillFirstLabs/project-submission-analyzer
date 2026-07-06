from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.db.database import get_db
from app.db.models import User, Submission, VivaSession
from app.services.auth import require_role

router = APIRouter(prefix="/mentor", tags=["Mentor Dashboard"])

@router.get("/submissions")
async def list_submissions(
    current_user: User = Depends(require_role("mentor")),
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Submission))
    submissions = result.scalars().all()
    
    # We also want to know the viva status for each
    viva_result = await db.execute(select(VivaSession))
    viva_sessions = {s.submission_id: s for s in viva_result.scalars().all()}
    
    response_data = []
    for sub in submissions:
        vs = viva_sessions.get(sub.id)
        response_data.append({
            "id": sub.id,
            "project_title": sub.project_title,
            "student_id": sub.student_id,
            "created_at": sub.created_at,
            "viva_status": vs.status if vs else "pending",
            "integrity_score": vs.integrity_score if vs else None,
            "risk_level": vs.risk_level if vs else None
        })
        
    return response_data
